from pathlib import Path
import os
PACKAGE_ROOT=Path(__file__).resolve().parents[2]
NATIVE_WORKSPACE=Path(os.environ.get("LST_NATIVE_WORKSPACE",str(PACKAGE_ROOT/"data/native_workspace"))).resolve()
import numpy as np,pandas as pd,json,hashlib,sys
B=NATIVE_WORKSPACE/'auxiliary/surface';R=B/'results';SIGMA=5.670374419e-8;SEED=20261028
f=pd.read_parquet(R/'full_matchups_common.parquet');KEYS=['station','design_date','target_hour'];PLAT=['noaa-goes16','noaa-goes17']
def temp(up,down,eps):return ((up-(1-eps)*down)/(eps*SIGMA))**.25

def metrics(e,w=None):
 if w is None:w=np.ones(len(e))
 return dict(bias=float(np.average(e,weights=w)),rmse=float(np.average(e**2,weights=w)**.5),mae=float(np.average(abs(e),weights=w)))

# Independent two-way cluster bootstrap; uncertainty from sparse site population remains explicit.
def boot(frame,vars,cluster='design_date',n=5000):
 sites=sorted(frame.station.unique());days=sorted(frame[cluster].unique());s=pd.Categorical(frame.station,categories=sites).codes;d=pd.Categorical(frame[cluster],categories=days).codes;rng=np.random.default_rng(SEED);out=[]
 for i in range(n):
  sc=np.bincount(rng.integers(len(sites),size=len(sites)),minlength=len(sites));dc=np.bincount(rng.integers(len(days),size=len(days)),minlength=len(days));w=sc[s]*dc[d]
  if w.sum()==0:continue
  row={'draw':i}
  for name in vars:
   e=frame[name].to_numpy();mm=metrics(e,w)
   for m,v in mm.items():row[name+'_'+m]=v
  if len(vars)==2:
   row['rmse_difference_G17_minus_G16']=row[vars[1]+'_rmse']-row[vars[0]+'_rmse'];row['bias_difference_G17_minus_G16']=row[vars[1]+'_bias']-row[vars[0]+'_bias']
  out.append(row)
 draws=pd.DataFrame(out);summary=[]
 for name in draws.columns[1:]:
  a=draws[name].to_numpy();summary.append({'cluster':cluster,'metric':name,'draws':len(a),'lower95':float(np.quantile(a,.025)),'upper95':float(np.quantile(a,.975))})
 return draws,summary

wide=f.pivot(index=KEYS,columns='bucket',values='residual_k').reset_index().rename(columns={PLAT[0]:'g16_error',PLAT[1]:'g17_error'});wide=wide.merge(f[KEYS+['event_id']].drop_duplicates(),on=KEYS,validate='one_to_one')
all_ci=[]
for unit in ['design_date','event_id']:
 draws,ci=boot(wide,['g16_error','g17_error'],unit);draws.to_parquet(R/f'raw_point_bootstrap_{unit}.parquet',index=False);all_ci+=ci
pd.DataFrame(all_ci).to_csv(R/'raw_point_cluster_bootstrap_summary.csv',index=False)

# Emissivity/irradiance scenarios are NOT probabilistic error bars or site-measured2021emissivities.
scenarios=[]
for name,ref in [('literature',f.ground_lst_k),('eps_minus_01',f.ground_lst_eps_minus01_k),('eps_plus_01',f.ground_lst_eps_plus01_k),('uniform_eps097',f.ground_lst_eps097_k),('nearest_ground_minute',f.ground_nearest_lst_k),('lw_up_plus5',temp(f.lw_up_mean+5,f.lw_down_mean,f.literature_eps)),('lw_up_minus5',temp(f.lw_up_mean-5,f.lw_down_mean,f.literature_eps)),('lw_down_plus5',temp(f.lw_up_mean,f.lw_down_mean+5,f.literature_eps)),('lw_down_minus5',temp(f.lw_up_mean,f.lw_down_mean-5,f.literature_eps))]:
 z=f.copy();z['scenario_ref']=ref
 for scope in ['all']+sorted(f.station.unique()):
  t=z if scope=='all' else z[z.station==scope]
  for bucket,y in t.groupby('bucket'):
   e=(y.point_lst_k-y.scenario_ref).to_numpy();m=metrics(e);scenarios.append(dict(scenario=name,scope=scope,bucket=bucket,n=len(e),**m,reference_shift_mean=float((y.scenario_ref-y.ground_lst_k).mean()),reference_shift_max_abs=float(abs(y.scenario_ref-y.ground_lst_k).max())))
pd.DataFrame(scenarios).to_csv(R/'radiometry_sensitivity_scenarios.csv',index=False)

# Symmetric station omission sensitivity, fixed before any claim about site skill.
loo=[]
for excluded in sorted(f.station.unique()):
 for bucket,y in f[f.station!=excluded].groupby('bucket'):loo.append(dict(excluded_station=excluded,bucket=bucket,n=len(y),**metrics(y.residual_k.to_numpy())))
pd.DataFrame(loo).to_csv(R/'leave_one_station_out.csv',index=False)

# Neighborhood comparison uses matched nonmissing3x3 estimates in BOTH platforms.
neighbors=f.pivot(index=KEYS,columns='bucket',values='neighborhood_mean_q0_k').dropna().reset_index()[KEYS]
z=f.merge(neighbors,on=KEYS,validate='many_to_one');ns=[]
for scope in ['all']+sorted(z.station.unique()):
 t=z if scope=='all' else z[z.station==scope]
 for bucket,y in t.groupby('bucket'):
  ns.append(dict(scope=scope,bucket=bucket,n=len(y),**metrics((y.neighborhood_mean_q0_k-y.ground_lst_k).to_numpy()),median_neighborhood_std_k=float(y.neighborhood_std_q0_k.median()),median_neighborhood_range_k=float(y.neighborhood_range_q0_k.median()),mean_point_to_neighbor_shift_k=float((y.neighborhood_mean_q0_k-y.point_lst_k).mean()),max_point_to_neighbor_shift_k=float(abs(y.neighborhood_mean_q0_k-y.point_lst_k).max())))
pd.DataFrame(ns).to_csv(R/'neighborhood_matched_sensitivity.csv',index=False)

# Station temporal change is explicitly NOT the study's core–ring transition.
tr=[]
for key,grp in f.groupby(['station','design_date','event_id','bucket']):
 pre=grp[grp.target_hour.isin([-3,-2,-1])];post=grp[grp.target_hour.isin([4,5,6])]
 if pre.target_hour.nunique()<2 or post.target_hour.nunique()<2:continue
 sat=float(post.point_lst_k.mean()-pre.point_lst_k.mean());ground=float(post.ground_lst_k.mean()-pre.ground_lst_k.mean());tr.append(dict(station=key[0],design_date=key[1],event_id=key[2],bucket=key[3],n_pre=len(pre),n_post=len(post),satellite_point_change_k=sat,ground_local_change_k=ground,residual_k=sat-ground))
tr=pd.DataFrame(tr);tr.to_csv(R/'station_pre_post_change.csv',index=False)
trmetrics=[]
if not tr.empty:
 for scope in ['all']+sorted(tr.station.unique()):
  t=tr if scope=='all' else tr[tr.station==scope]
  for bucket,y in t.groupby('bucket'):trmetrics.append(dict(scope=scope,bucket=bucket,n=len(y),days=y.design_date.nunique(),**metrics(y.residual_k.to_numpy())))
 pd.DataFrame(trmetrics).to_csv(R/'station_pre_post_change_metrics.csv',index=False)
 tw=tr.pivot(index=['station','design_date','event_id'],columns='bucket',values='residual_k').dropna().reset_index().rename(columns={PLAT[0]:'g16_error',PLAT[1]:'g17_error'})
 for cluster in ['design_date','event_id']:
  draws,ci=boot(tw,['g16_error','g17_error'],cluster);draws.to_parquet(R/f'station_change_bootstrap_{cluster}.parquet',index=False);pd.DataFrame(ci).to_csv(R/f'station_change_bootstrap_{cluster}_summary.csv',index=False)

# Attrition remains in available/requested denominators and all3sites remain visible.
requests=pd.read_csv(R/'full_requests_all.csv');allrows=pd.read_parquet(R/'full_matchups_all.parquet');attr=[]
for code in ['all']+sorted(requests.station.unique()):
 rq=requests if code=='all' else requests[requests.station==code];av=allrows if code=='all' else allrows[allrows.station==code];co=f if code=='all' else f[f.station==code]
 for bucket in PLAT:
  a=rq[rq.bucket==bucket];b=av[av.bucket==bucket];c=co[co.bucket==bucket]
  attr.append(dict(station=code,bucket=bucket,requested=len(a),native_present=len(b),native_missing=int(a.key.isna().sum()),point_dqf0_physical=int(b.point_valid_q0.sum()),ground_qc0=int(b.ground_valid.sum()),common_matchups=len(c)))
pd.DataFrame(attr).to_csv(R/'attrition_by_station_platform.csv',index=False)
# Exact historical flags in scan neighborhood and representative footprint size.
pd.crosstab(allrows.station,allrows.point_dqf).to_csv(R/'point_dqf_counts.csv')
foot=allrows.groupby(['station','bucket'])[['center_distance_m','pixel_spacing_x_m','pixel_spacing_y_m']].agg(['min','max']).reset_index();foot.to_csv(R/'station_pixel_geometry.csv',index=False)

out=dict(common_matchups=len(f)//2,common_stations=f.station.nunique(),common_design_days=f.design_date.nunique(),common_intervals=f.event_id.nunique(),station_change_matchups=len(tr)//2,station_change_days=tr.design_date.nunique() if not tr.empty else 0,primary_point_ci=all_ci,sensitivity_scenarios=scenarios,station_change_metrics=trmetrics,attrition=attr,limitations=['Assumed historical broadbandemissivity,not measured2021values;epsilonand±5W/m²are scenarios,not completeuncertaintyconfidencebounds.','DirectionalABIpixeland hemisphericallocalradiometer have differentfootprints;3×3variationdoesnotproveequivalence.','DRApublishedpost2018IRstabilityconcernpreventsinterpretingitshighsharederrorssolelyassatelliteerror;all3stationsretained.','Only3sitesand4eightdaywindows;clusterintervalscannotestablishpopulationwideperformance.','No city-trainedcorrectionapplied;no groundurban-core/ringcontrastconstructed.','Repairedcivil-local-datesunsetallocation;actualsunsetdateequalsdesignlabel.'])
(R/'benchmark_final_summary.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['primary_point_ci','sensitivity_scenarios']},indent=2))
