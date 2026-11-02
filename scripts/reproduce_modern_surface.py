"""Recompute modern station metrics/sensitivities/bootstrap from packaged pairs.

Requires Python>=3.9, numpy and pandas. No native downloads, no fitting, no
absolute host paths. Raw verification is a separate recorded, executed audit.
"""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd

parser=argparse.ArgumentParser()
parser.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parents[1]/'02_EVIDENCE/surface/modern')
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--verify-against',type=Path)
args=parser.parse_args();D=args.data_dir;O=args.output_dir;O.mkdir(parents=True,exist_ok=True)
f=pd.read_csv(D/'full_matchups_common.csv');KEY=['station','design_date','target_hour'];SITES=['dra','fpk','tbl'];SIGMA=5.670374419e-8
assert not f.duplicated(KEY+['bucket']).any() and f.groupby(KEY).size().eq(2).all()
assert f.point_dqf.isin([0,1]).all() and f.ground_qc0_minutes.ge(12).all() and f.platform_scan_separation_seconds.le(60).all()
def metric(e):
 e=np.asarray(e,float);return dict(n=len(e),bias_K=float(e.mean()),rmse_K=float(np.linalg.norm(e)/np.sqrt(len(e))),mae_K=float(abs(e).mean()))
metrics=[];scenarios=[];intervals=[]
for year,z in f.groupby('year'):
 for site in ['pooled']+SITES:
  t=z if site=='pooled' else z[z.station.eq(site)]
  for bucket,g in t.groupby('bucket'):metrics.append(dict(year=int(year),station=site,bucket=bucket,dates=g.design_date.nunique(),**metric(g.point_lst_k-g.ground_lst_k)))
 refs={'literature':z.ground_lst_k,'eps_plus01':z.ground_lst_eps_plus01_k,'eps_minus01':z.ground_lst_eps_minus01_k,'uniform_eps097':z.ground_lst_eps097_k,'nearest_ground_minute':z.ground_nearest_lst_k}
 for tag,du,dd in [('lw_up_plus5',5,0),('lw_up_minus5',-5,0),('lw_down_plus5',0,5),('lw_down_minus5',0,-5)]:refs[tag]=((z.lw_up_mean+du-(1-z.literature_eps)*(z.lw_down_mean+dd))/(z.literature_eps*SIGMA))**.25
 for tag,ref in refs.items():
  t=z.copy();t['scenario_ref']=ref
  for bucket,g in t.groupby('bucket'):scenarios.append(dict(year=year,scenario=tag,bucket=bucket,**metric(g.point_lst_k-g.scenario_ref),mean_reference_shift_K=float((g.scenario_ref-g.ground_lst_k).mean()),max_abs_reference_shift_K=float(abs(g.scenario_ref-g.ground_lst_k).max())))
 w=z.pivot(index=KEY+['event_id'],columns='bucket',values='residual_k').reset_index();sites=sorted(w.station.unique())
 for cluster in ['design_date','event_id']:
  cats=sorted(w[cluster].unique());sc=pd.Categorical(w.station,categories=sites).codes;dc=pd.Categorical(w[cluster],categories=cats).codes;es=[w['noaa-goes18'].to_numpy(),w['noaa-goes19'].to_numpy()]
  rng=np.random.default_rng(20261029);rr=[]
  for k in range(5000):
   sw=np.bincount(rng.integers(len(sites),size=len(sites)),minlength=len(sites));cw=np.bincount(rng.integers(len(cats),size=len(cats)),minlength=len(cats));wt=sw[sc]*cw[dc]
   if not wt.sum():continue
   a,b=[np.sqrt(np.sum(wt*e*e)/wt.sum()) for e in es];rr.append((a,b,b-a))
  rr=np.asarray(rr)
  for j,name in enumerate(['G18_RMSE_K','G19_RMSE_K','G19_minus_G18_RMSE_K']):
   lo,hi=np.quantile(rr[:,j],[.025,.975]);intervals.append(dict(year=year,cluster=cluster,metric=name,draws=len(rr),ci95_low_K=lo,ci95_high_K=hi))
pd.DataFrame(metrics).to_csv(O/'compact_station_metrics.csv',index=False);pd.DataFrame(scenarios).to_csv(O/'modern_ground_sensitivity.csv',index=False);pd.DataFrame(intervals).to_csv(O/'modern_bootstrap_intervals.csv',index=False)
native=pd.read_csv(D/'independent_point_quality_geometry.csv');nf=f.merge(native[KEY+['bucket','neighborhood_mean_q01_K','neighborhood_n_q01']],on=KEY+['bucket'],validate='one_to_one');valid=nf.groupby(KEY).neighborhood_mean_q01_K.count();nf=nf.merge(valid[valid==2].reset_index()[KEY],on=KEY,validate='many_to_one');ns=[]
for year,z in nf.groupby('year'):
 for bucket,g in z.groupby('bucket'):
  p=metric(g.point_lst_k-g.ground_lst_k);ns.append(dict(year=year,bucket=bucket,**metric(g.neighborhood_mean_q01_K-g.ground_lst_k),matched_point_bias_K=p['bias_K'],matched_point_rmse_K=p['rmse_K']))
pd.DataFrame(ns).to_csv(O/'modern_neighborhood_sensitivity.csv',index=False)
checks=[]
if args.verify_against:
 for name in ['compact_station_metrics.csv','modern_ground_sensitivity.csv','modern_bootstrap_intervals.csv','modern_neighborhood_sensitivity.csv']:
  a=pd.read_csv(O/name);b=pd.read_csv(args.verify_against/name);assert a.shape==b.shape and list(a)==list(b),(name,a.shape,b.shape)
  maxerr=0.
  for c in a:
   if pd.api.types.is_numeric_dtype(a[c]):
    e=float(np.max(np.abs(a[c].to_numpy()-b[c].to_numpy())));maxerr=max(maxerr,e);assert np.allclose(a[c],b[c],rtol=1e-11,atol=1e-10,equal_nan=True),(name,c,e)
   else:assert a[c].fillna('').eq(b[c].fillna('')).all(),(name,c)
  checks.append(dict(file=name,rows=len(a),columns=len(a.columns),max_abs_numeric_difference=maxerr,status='PASS'))
out=dict(status='PASS',common_pairs=len(f)//2,years={str(y):int(len(z)//2) for y,z in f.groupby('year')},checks=checks,scope='Offline regeneration from packaged station pairs and retained neighborhood values; native/raw ground decoding not repeated by this command.')
(O/'offline_reproduction.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
