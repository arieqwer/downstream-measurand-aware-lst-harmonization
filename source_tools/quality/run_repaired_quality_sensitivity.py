"""Fixed-model 2026 quality sensitivity. No fitting, no provider downloads."""
from pathlib import Path
import os
PACKAGE_ROOT=Path(__file__).resolve().parents[2]
NATIVE_WORKSPACE=Path(os.environ.get("LST_NATIVE_WORKSPACE",str(PACKAGE_ROOT/"data/native_workspace"))).resolve()
import hashlib,json,sys,time
import numpy as np
import pandas as pd
import joblib,sklearn,pyarrow
OUT=NATIVE_WORKSPACE/'auxiliary/quality'
(OUT/'results').mkdir(parents=True,exist_ok=True)
SCI=Path(os.environ.get('LST_REPRODUCTION_OUTPUT',str(PACKAGE_ROOT/'outputs/reproduced')))/'repaired'
EXTRACTION=PACKAGE_ROOT/'data/corrected_inputs'
sys.path.insert(0,str(PACKAGE_ROOT/'scripts'))
sys.path.append(str(PACKAGE_ROOT/'scripts'))
from train_goes18_goes19_metric_harmonization import predict_hourly, predict_transition
MODEL=SCI/'outputs/grl_deepening_2026/goes18_goes19_metric_harmonization'
PATHS={
 'reference':EXTRACTION/'goes18_2026_metric_holdout/goes_sunset_hourly.parquet',
 'source':EXTRACTION/'goes19_2026_metric_holdout/goes_sunset_hourly.parquet',
 'baseline_hourly':MODEL/'validation_2026_hourly_predictions.parquet',
 'baseline_transition':MODEL/'validation_2026_transition_predictions.parquet',
 'model':MODEL/'frozen_metric_aware_model.joblib',
}
KEYS=['uc_id','event_year','event_step8','event_time_id','target_hour_from_sunset']
DAILY=[*KEYS,'local_date']; TRANS=KEYS[:-1]
SEED=20260810;DRAWS=5000
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={k:dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for k,p in PATHS.items()}
t0=time.monotonic()
original=pd.read_parquet(PATHS['baseline_hourly']);original.uc_id=original.uc_id.astype(str)
original_t=pd.read_parquet(PATHS['baseline_transition']);original_t.uc_id=original_t.uc_id.astype(str)
model=joblib.load(PATHS['model'])
selected_names={k:v['name'] for k,v in model['hourly'].items()}
print('REPAIRED_MODEL_NAMES',selected_names,model['transition']['name'],flush=True)
FEATURES=['lat','lon','vza_target','vza_source','vza_difference','vza_mean','calibration_cohort']
assert original.groupby('uc_id')[FEATURES].nunique().max().max()==1
geometry=original[['uc_id',*FEATURES]].drop_duplicates('uc_id')
raw={}
for sensor in ['reference','source']:
 f=pd.read_parquet(PATHS[sensor]);f.uc_id=f.uc_id.astype(str)
 assert not f.duplicated(DAILY).any()
 cols=[*DAILY,'scan_time_utc','sunset_utc','source_key']+[f'{u}_{qa}_{s}' for u in ['core','ring'] for qa in ['strict','recommended'] for s in ['count','lst_k']]
 raw[sensor]=f[cols].rename(columns={c:c+'_'+sensor for c in cols if c not in DAILY})
pair=raw['reference'].merge(raw['source'],on=DAILY,validate='one_to_one')
pair['scan_offset_min']=(pd.to_datetime(pair.scan_time_utc_reference,utc=True,format='mixed')-pd.to_datetime(pair.scan_time_utc_source,utc=True,format='mixed')).dt.total_seconds().abs()/60
for qa in ['recommended','strict']:
 valid=pair.scan_offset_min.lt(1)
 for sensor in ['reference','source']:
  for u,n in [('core',3),('ring',10)]:
   valid &= pair[f'{u}_{qa}_count_{sensor}'].ge(n)&pair[f'{u}_{qa}_lst_k_{sensor}'].between(180,380)
 pair['valid_'+qa]=valid
pair['valid_common']=pair.valid_recommended&pair.valid_strict
SCENARIOS={'recommended_full':('recommended','valid_recommended'),'strict_full':('strict','valid_strict'),'recommended_common_daily':('recommended','valid_common'),'strict_common_daily':('strict','valid_common')}

def features(f):
 hour=pd.get_dummies(f.target_hour_from_sunset.astype(int),prefix='hour',dtype=float).reindex(columns=[f'hour_{h}' for h in range(-3,7)],fill_value=0.0).reset_index(drop=True)
 geo=f[['lat','lon','vza_target','vza_source','vza_difference','vza_mean']].astype(float).reset_index(drop=True)
 return pd.concat([hour,geo],axis=1)

def aggregate(qa,valid):
 p=pair.loc[pair[valid]]
 f=p.groupby(KEYS,observed=True).agg(n_paired_days=('local_date','nunique'),scan_offset_min=('scan_offset_min','mean'),**{f'{s}_{u}':(f'{u}_{qa}_lst_k_{i}','mean') for s,i in [('target','reference'),('source','source')] for u in ['core','ring']}).reset_index()
 f=f.merge(geometry,on='uc_id',validate='many_to_one')
 assert not f[FEATURES].isna().any().any()
 f['source_anomaly']=f.source_core-f.source_ring
 f['target_anomaly']=f.target_core-f.target_ring
 for component in ['core','ring']:f['pred_'+component]=predict_hourly(model['hourly'][component],f)
 f['selected_anomaly']=predict_hourly(model['hourly']['anomaly'],f)
 for s in ['target','source','pred']:f[s+'_contrast']=f[s+'_core']-f[s+'_ring']
 return f

def transition(f):
 columns=[f'{s}_{u}' for s in ['target','source','pred'] for u in ['core','ring','contrast']]
 def window(hours,label):
  x=f[f.target_hour_from_sunset.isin(hours)]
  z=x.groupby(TRANS,observed=True).agg(n_hours=('target_hour_from_sunset','nunique'),**{c:(c,'mean') for c in columns}).reset_index()
  z=z[z.n_hours.ge(2)]
  return z.rename(columns={c:c+'_'+label for c in ['n_hours',*columns]})
 z=window([-3,-2,-1],'pre').merge(window([4,5,6],'post'),on=TRANS,validate='one_to_one')
 for c in columns:z[c]=z[c+'_post']-z[c+'_pre']
 # The directly selected transition uses the repaired calibration choice; component-derived transition is distinct.
 z=z.merge(geometry,on='uc_id',validate='many_to_one')
 z['source_anomaly_transition']=z.source_contrast;z['target_anomaly_transition']=z.target_contrast
 z['source_core_transition']=z.source_core;z['source_ring_transition']=z.source_ring
 z['source_anomaly_pre']=z.source_core_pre-z.source_ring_pre;z['source_anomaly_late']=z.source_core_post-z.source_ring_post
 z['source_surface_pre']=(z.source_core_pre+z.source_ring_pre)/2;z['source_surface_late']=(z.source_core_post+z.source_ring_post)/2
 z['selected_transition']=predict_transition(model['transition'],z)
 z['covered']=(np.abs(z.selected_transition-z.target_contrast)<=float(model['transition_uncertainty_half_width_k']))
 z['sign_supported']=(np.abs(z.selected_transition)>float(model['transition_uncertainty_half_width_k']))
 z['sign_matching']=np.sign(z.selected_transition)==np.sign(z.target_contrast)
 return z
frames={};summaries=[]
for label,(qa,valid) in SCENARIOS.items():
 h=aggregate(qa,valid);t=transition(h);frames[label]={'hourly':h,'transition':t}
 h.to_parquet(OUT/'results'/f'{label}_hourly.parquet',index=False);t.to_parquet(OUT/'results'/f'{label}_transition.parquet',index=False)
 summaries.append(dict(scenario=label,paired_daily_rows=int(pair[valid].sum()),hourly_rows=len(h),cities=h.uc_id.nunique(),intervals=h.event_time_id.nunique(),transitions=len(t),transition_cities=t.uc_id.nunique(),max_daily_scan_gap_min=float(pair.loc[pair[valid],'scan_offset_min'].max())))
# Additional controlled stage: original recommended data, all dates, but only cities
# surviving strict QA. This separates city attrition from within-city daily support.
eligible_cities=set(frames['strict_full']['hourly'].uc_id.unique())
name='recommended_eligible_city_full_dates'
h=frames['recommended_full']['hourly'].loc[lambda f:f.uc_id.isin(eligible_cities)].copy();t=transition(h)
frames[name]={'hourly':h,'transition':t}
h.to_parquet(OUT/'results'/f'{name}_hourly.parquet',index=False);t.to_parquet(OUT/'results'/f'{name}_transition.parquet',index=False)
summaries.append(dict(scenario=name,paired_daily_rows=int((pair.valid_recommended&pair.uc_id.isin(eligible_cities)).sum()),hourly_rows=len(h),cities=h.uc_id.nunique(),intervals=h.event_time_id.nunique(),transitions=len(t),transition_cities=t.uc_id.nunique(),max_daily_scan_gap_min=float(pair.loc[pair.valid_recommended&pair.uc_id.isin(eligible_cities),'scan_offset_min'].max())))
# Baseline replay must pass before sensitivity statistics are computed.
base=frames['recommended_full']['hourly'].merge(original,on=KEYS,suffixes=('_replay','_original'),validate='one_to_one')
assert len(base)==len(original) and original.event_time_id.nunique()==8
errors={c:float(np.abs(base[c+'_replay']-base[c+'_original']).max()) for c in ['target_core','target_ring','source_core','source_ring','pred_core','pred_ring']}
assert max(errors.values())<1e-10
comparison_columns=['target_core','target_ring','source_core','source_ring','pred_core','pred_ring']
original_comparison=original_t[TRANS+[c+'_transition' for c in comparison_columns]].rename(columns={c+'_transition':'baseline_'+c for c in comparison_columns})
bt=frames['recommended_full']['transition'].merge(original_comparison,on=TRANS,validate='one_to_one')
assert len(bt)==len(original_t)
terror={c:float(np.abs(bt[c]-bt['baseline_'+c]).max()) for c in comparison_columns}
assert max(terror.values())<1e-10
h1=frames['recommended_common_daily']['hourly'];h2=frames['strict_common_daily']['hourly']
assert h1[KEYS].equals(h2[KEYS]) and h1.n_paired_days.equals(h2.n_paired_days)
assert frames['recommended_common_daily']['transition'][TRANS].equals(frames['strict_common_daily']['transition'][TRANS])
print('BASELINE REPLAY PASS',json.dumps(dict(hourly=errors,transition=terror)),flush=True)

# Error-vector sufficient statistics [n,sum a,b,c,d,sum a²,b²,c²,d²,sum ab,cd].
def error_array(f):return np.column_stack([f.source_core-f.target_core,f.source_ring-f.target_ring,f.pred_core-f.target_core,f.pred_ring-f.target_ring]).astype(float)
def stats_from_totals(v):
 n=v[0];mu=v[1:5]/n;ms=v[5:9]/n;cov=v[9:11]/n-np.array([mu[0]*mu[1],mu[2]*mu[3]])
 variance=ms-mu*mu;dr=ms[0]+ms[1]-2*v[9]/n;dh=ms[2]+ms[3]-2*v[10]/n
 vg=variance[0]+variance[1]-variance[2]-variance[3];bg=(mu[0]-mu[1])**2-(mu[2]-mu[3])**2;cp=2*(cov[0]-cov[1]);gain=dr-dh
 assert abs(gain-vg-bg+cp)<1e-10
 return dict(raw_core_bias_K=mu[0],raw_ring_bias_K=mu[1],corrected_core_bias_K=mu[2],corrected_ring_bias_K=mu[3],raw_core_variance_K2=variance[0],raw_ring_variance_K2=variance[1],corrected_core_variance_K2=variance[2],corrected_ring_variance_K2=variance[3],raw_core_rmse_K=np.sqrt(max(0,ms[0])),raw_ring_rmse_K=np.sqrt(max(0,ms[1])),corrected_core_rmse_K=np.sqrt(max(0,ms[2])),corrected_ring_rmse_K=np.sqrt(max(0,ms[3])),raw_contrast_rmse_K=np.sqrt(max(0,dr)),corrected_contrast_rmse_K=np.sqrt(max(0,dh)),raw_covariance_K2=cov[0],corrected_covariance_K2=cov[1],variance_gain_K2=vg,differential_bias_gain_K2=bg,covariance_loss_penalty_K2=cp,net_contrast_mse_gain_K2=gain,contrast_RMSE_reduction_percent=100*(1-np.sqrt(max(0,dh/dr))) if dr>0 else np.nan,contrast_MSE_gain_percent=100*gain/dr if dr>0 else np.nan,identity_residual_K2=gain-vg-bg+cp)
def total(e,w=None):
 if w is None:w=np.ones(len(e))
 return np.r_[w.sum(),np.sum(e*w[:,None],axis=0),np.sum(e*e*w[:,None],axis=0),np.sum(e[:,0]*e[:,1]*w),np.sum(e[:,2]*e[:,3]*w)]
def stats(f):
 e=error_array(f);out=stats_from_totals(total(e));out.update(n=len(f),cities=f.uc_id.nunique(),intervals=f.event_time_id.nunique())
 # Independent direct error and covariance computation.
 dc=float(np.mean((e[:,0]-e[:,1])**2));hc=float(np.mean((e[:,2]-e[:,3])**2));assert abs(dc-hc-out['net_contrast_mse_gain_K2'])<1e-10
 vv=np.zeros((e.shape[1],e.shape[1])) if len(e)==1 else np.cov(e,rowvar=False,bias=True);b=e.mean(axis=0)
 assert abs(dc-(vv[0,0]+vv[1,1]-2*vv[0,1]+(b[0]-b[1])**2))<1e-10
 if 'covered' in f:
  out.update(fixed_interval_coverage_percent=100*f.covered.mean(),fixed_interval_sign_support_percent=100*f.sign_supported.mean(),fixed_interval_supported_sign_match_percent=100*f.loc[f.sign_supported,'sign_matching'].mean(),sign_supported_n=int(f.sign_supported.sum()))
 return out
points=[];metrics=[];strata=[]
for label,levels in frames.items():
 for level,f in levels.items():
  x=stats(f);points.append(dict(scenario=label,level=level,**x))
  for component in ['core','ring','contrast']:
   for phase in ['raw','corrected']:
    pred=f[('source_' if phase=='raw' else 'pred_')+component];err=(pred-f['target_'+component]).to_numpy()
    metrics.append(dict(scenario=label,level=level,component=component,phase=phase,n=len(f),bias_K=float(err.mean()),mae_K=float(np.abs(err).mean()),rmse_K=float(np.sqrt(np.mean(err*err)))))
  dims=['uc_id','event_time_id']+(['target_hour_from_sunset','calibration_cohort'] if level=='hourly' else [])
  for dim in dims:
   for group,sub in f.groupby(dim,observed=True):strata.append(dict(scenario=label,level=level,dimension=dim,stratum=str(group),**stats(sub)))
pd.DataFrame(summaries).to_csv(OUT/'results/support_summary.csv',index=False);pd.DataFrame(points).to_csv(OUT/'results/full_mse_decompositions.csv',index=False);pd.DataFrame(metrics).to_csv(OUT/'results/component_and_contrast_metrics.csv',index=False);pd.DataFrame(strata).to_csv(OUT/'results/stratified_performance.csv',index=False)
# Attrition counted at the daily support stage, before averaging.
attr=[]
for dim in ['uc_id','event_time_id','target_hour_from_sunset']:
 for group,p in pair.groupby(dim,observed=True):
  attr.append(dict(dimension=dim,stratum=str(group),paired_candidates=len(p),recommended_retained=int(p.valid_recommended.sum()),strict_retained=int(p.valid_strict.sum()),common_retained=int(p.valid_common.sum()),recommended_rejected=len(p)-int(p.valid_recommended.sum()),strict_rejected=len(p)-int(p.valid_strict.sum())))
pd.DataFrame(attr).to_csv(OUT/'results/daily_attrition.csv',index=False)
pair.to_parquet(OUT/'results/paired_daily_regional_summaries.parquet',index=False)
pair[[*DAILY,'scan_offset_min','valid_recommended','valid_strict','valid_common','sunset_utc_reference','sunset_utc_source','source_key_reference','source_key_source','scan_time_utc_reference','scan_time_utc_source']].to_parquet(OUT/'results/daily_pair_support.parquet',index=False)

# Independent synthetic check with nonuniform weights and an exactly known differential bias.
e=np.array([[3.,1.,0.,0.],[3.,1.,0.,0.],[3.,1.,0.,0.]])
assert abs(stats_from_totals(total(e))['net_contrast_mse_gain_K2']-4)<1e-12
w=np.array([1,3,2]);assert np.allclose(total(e,w),total(np.repeat(e,w,axis=0)),atol=1e-12)
BOOTSCENARIOS=['recommended_eligible_city_full_dates','recommended_common_daily','strict_common_daily']
cities=sorted(eligible_cities);intervals=sorted(original.event_time_id.unique());cells=pd.MultiIndex.from_product([cities,intervals],names=['uc_id','event_time_id'])
matrices={}
for level in ['hourly','transition']:
 for label in BOOTSCENARIOS:
  f=frames[label][level];e=error_array(f);v=np.column_stack([np.ones(len(f)),e,e*e,e[:,0]*e[:,1],e[:,2]*e[:,3]])
  tmp=pd.DataFrame(v);tmp['uc_id']=f.uc_id.to_numpy();tmp['event_time_id']=f.event_time_id.to_numpy();a=tmp.groupby(['uc_id','event_time_id'],observed=True).sum().reindex(cells,fill_value=0).to_numpy(float)
  matrices[(level,label)]=a
rng=np.random.default_rng(SEED);draw_rows=[];diff_rows=[]
METRICS=['raw_core_rmse_K','corrected_core_rmse_K','raw_ring_rmse_K','corrected_ring_rmse_K','raw_contrast_rmse_K','corrected_contrast_rmse_K','variance_gain_K2','differential_bias_gain_K2','covariance_loss_penalty_K2','net_contrast_mse_gain_K2','contrast_RMSE_reduction_percent','contrast_MSE_gain_percent']
COMPARISONS={'quality_on_common_daily_support':('strict_common_daily','recommended_common_daily'),'daily_support_selection_within_eligible_cities':('recommended_common_daily','recommended_eligible_city_full_dates'),'total_within_eligible_cities':('strict_common_daily','recommended_eligible_city_full_dates')}
for draw in range(DRAWS):
 cw=rng.multinomial(len(cities),np.repeat(1/len(cities),len(cities)));iw=rng.multinomial(len(intervals),np.repeat(1/len(intervals),len(intervals)));weights=(cw[:,None]*iw[None,:]).ravel()
 for level in ['hourly','transition']:
  rows={}
  for label in BOOTSCENARIOS:
   v=weights@matrices[(level,label)];assert v[0]>0
   x=stats_from_totals(v);rows[label]=x
   draw_rows.append(dict(draw=draw,level=level,scenario=label,**{m:x[m] for m in METRICS}))
   if draw==0:
    f=frames[label][level];idx=cells.get_indexer(pd.MultiIndex.from_frame(f[['uc_id','event_time_id']]));expanded=total(np.repeat(error_array(f),weights[idx],axis=0));assert np.allclose(v,expanded,atol=1e-9,rtol=1e-12)
  for name,(later,earlier) in COMPARISONS.items():diff_rows.append(dict(draw=draw,level=level,comparison=name,**{m:rows[later][m]-rows[earlier][m] for m in METRICS}))
 if draw%1000==0:print('bootstrap',draw,'/',DRAWS,flush=True)
draw_df=pd.DataFrame(draw_rows);diff_df=pd.DataFrame(diff_rows);draw_df.to_parquet(OUT/'results/paired_crossed_bootstrap_draws.parquet',index=False);diff_df.to_parquet(OUT/'results/paired_crossed_bootstrap_differences.parquet',index=False)
ci=[];delta=[]
point_index={(x['level'],x['scenario']):x for x in points}
for (level,label),df in draw_df.groupby(['level','scenario']):
 for m in METRICS:ci.append(dict(level=level,scenario=label,metric=m,observed=point_index[(level,label)][m],lower_95=float(df[m].quantile(.025)),upper_95=float(df[m].quantile(.975)),bootstrap_draws=DRAWS))
for (level,name),df in diff_df.groupby(['level','comparison']):
 later,earlier=COMPARISONS[name]
 for m in METRICS:delta.append(dict(level=level,comparison=name,later_scenario=later,earlier_scenario=earlier,metric=m,observed_difference=point_index[(level,later)][m]-point_index[(level,earlier)][m],lower_95=float(df[m].quantile(.025)),upper_95=float(df[m].quantile(.975)),bootstrap_draws=DRAWS))
pd.DataFrame(ci).to_csv(OUT/'results/paired_crossed_bootstrap_summary.csv',index=False);pd.DataFrame(delta).to_csv(OUT/'results/paired_crossed_bootstrap_comparison_summary.csv',index=False)
for k,p in PATHS.items():assert sha(p)==inputs[k]['sha256']
manifest=dict(command='/usr/bin/python3 '+str(Path(__file__).resolve()),python=sys.version,numpy=np.__version__,pandas=pd.__version__,scikit_learn=sklearn.__version__,pyarrow=pyarrow.__version__,joblib=joblib.__version__,seed=SEED,bootstrap_draws=DRAWS,bootstrap_population=dict(cities=cities,n_city_clusters=len(cities),intervals=[int(x) for x in intervals],scope=f'conditional on{len(cities)}strict-eligiblecities; fullpopulation{original.uc_id.nunique()}citiescomparisonisdescriptive'),inputs=inputs,script_sha256=sha(Path(__file__)),elapsed_seconds=time.monotonic()-t0,acceptance=dict(replayed_hourly_rows=len(base),replayed_transition_rows=len(bt),hourly_max_abs_replay_error_K=max(errors.values()),transition_max_abs_replay_error_K=max(terror.values()),component_predictions_unchanged=True,baseline_verified=True,common_daily_and_transition_keys_equal=True,weighted_explicit_repeat_control_pass=True,independent_covariance_identity_pass=True,original_inputs_unchanged=True),support=summaries,limitations=[f'Strict screening retains{len(cities)}cities. Bootstrap intervals condition ontheseeligiblecities,notfull{original.uc_id.nunique()}citypopulation; sparseclusterslimitinference.', 'Usesrepairedphysical-local-datesandcompletepolygonmaskswithrefitted2025models;newbaselinepredictreplayrequired.', 'Fixedmodelswerecalibratedonrepairedrecommended-qualitydata;nostrict-qualityrecalibrationisperformed.','Both source and reference regional means change under strict QA. This remains an inter-platform consistency sensitivity, not absolute accuracy.','Common eligible daily support fixes dates and resulting hourly keys, not the identities of pixels within each regional mean.','DQF sensitivity is not an independent alternative cloud-mask experiment.','Raw native flag meanings require metadata confirmation before interpreting codes as high/medium quality.','Bootstrap intervals describe paired sensitivity contrasts, not model selection or causal effects.'])
(OUT/'results/validation_manifest.json').write_text(json.dumps(manifest,indent=2));print(pd.DataFrame(points)[['scenario','level','n','raw_core_rmse_K','corrected_core_rmse_K','raw_ring_rmse_K','corrected_ring_rmse_K','raw_contrast_rmse_K','corrected_contrast_rmse_K','net_contrast_mse_gain_K2','contrast_RMSE_reduction_percent']].to_string(index=False));print('PASS',time.monotonic()-t0,'seconds',flush=True)
