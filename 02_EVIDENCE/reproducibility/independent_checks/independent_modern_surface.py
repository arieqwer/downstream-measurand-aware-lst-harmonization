from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib,json
import numpy as np,pandas as pd
O=Path('/Users/apple/Downloads/RS revision 1/continuation_20261029/science/claims_audit');B=O.parent/'modern_surface/recommended/results'
p=B/'full_matchups_common.csv';f=pd.read_csv(p);M=pd.read_csv(B/'full_metrics.csv');checks=[];metrics=[]
def check(n,ok,d=None):checks.append(dict(name=n,passed=bool(ok),details=d))
keys=['station','design_date','target_hour'];check('Unique platform/time keys',not f.duplicated(keys+['bucket']).any());check('Two platforms per common key',f.groupby(keys).bucket.nunique().eq(2).all());check('282commonpairs',len(f)==564 and len(f.groupby(keys))==282)
check('Only native0/1 modern tier',f.point_dqf.isin([0,1]).all());check('Every common G19point is tier1',f[f.bucket.eq('noaa-goes19')].point_dqf.eq(1).all());check('No strict common support',not f.groupby(keys).point_dqf.max().eq(0).any())
check('Ground windowQC12of15',f.ground_qc0_minutes.ge(12).all() and f.ground_total_minutes.eq(15).all() and f.ground_valid.all());check('Native physicalbounds',f.point_lst_k.between(180,380).all());check('Native scan gap<1minute',f.platform_scan_separation_seconds.lt(60).all());check('Finite common temperatures',np.isfinite(f[['point_lst_k','ground_lst_k']]).all().all())
ground=((f.lw_up_mean-(1-f.literature_eps)*f.lw_down_mean)/(f.literature_eps*5.670374419e-8))**.25
check('Ground radiometry independently recomputed',np.allclose(ground,f.ground_lst_k,atol=1e-10,rtol=0),float(np.max(abs(ground-f.ground_lst_k))))
check('Residuals independently recomputed',np.allclose(f.point_lst_k-ground,f.residual_k,atol=1e-10,rtol=0))
for site,g in f.groupby('station'):
 local=pd.to_datetime(g.sunset_utc,utc=True,format='mixed').dt.tz_convert(ZoneInfo('America/Los_Angeles' if site=='dra' else 'America/Denver')).dt.strftime('%Y-%m-%d')
 check(site+' physical local sunset date',np.array_equal(local,g.design_date))
check('18first-localdates',f.design_date.nunique()==18 and f[f.year.eq(2025)].design_date.nunique()==10 and f[f.year.eq(2026)].design_date.nunique()==8)
for yr in ['all',2025,2026]:
 y=f if yr=='all' else f[f.year.eq(yr)]
 for site in ['all','dra','fpk','tbl']:
  g=y if site=='all' else y[y.station.eq(site)]
  for bucket,z in g.groupby('bucket'):
   e=(z.point_lst_k-z.ground_lst_k).to_numpy();r=dict(year=yr,site=site,bucket=bucket,n=len(z),dates=z.design_date.nunique(),bias=float(e.mean()),RMSE=float(np.sqrt(np.mean(e**2))))
   metrics.append(r)
   if yr=='all':
    actual=M[M.dimension.eq('pooled' if site=='all' else 'station')&M.group.eq(site)&M.bucket.eq(bucket)].iloc[0]
   elif site=='all':actual=M[M.dimension.eq('year')&M.group.eq(str(yr))&M.bucket.eq(bucket)].iloc[0]
   else:continue
   check(str(yr)+' '+site+' '+bucket+' pointmetrics',actual.n==r['n'] and abs(actual.bias-r['bias'])<1e-10 and abs(actual.rmse-r['RMSE'])<1e-10)
pd.DataFrame(metrics).to_csv(O/'independent_modern_station_metrics.csv',index=False)
out=dict(status='PASS' if all(x['passed'] for x in checks) else 'FAIL',checks=checks,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest(),str(B/'full_metrics.csv'):hashlib.sha256((B/'full_metrics.csv').read_bytes()).hexdigest()},metrics=metrics,interpretation='Rigorous descriptive extension is feasible under declared primary modernDQF0/1tier, with282commonpairs on18sampledfirst-localdays at3sites. All G19paired pixels haveDQF1; strict0jointsupport iszero. Historicalstrict0andmodern0/1resultsdo notsupportacrosseraranking. Fullurbanworkflowgroundvalidationremainsincomplete.',scope='Independent scalar/support/ground-flux formula audit of final per-matchup table. Provider-native decode and minute QC reconstruction are separately checked by surface agent; not re-executed in this script.')
(O/'independent_modern_surface_results.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(status=out['status'],checks=len(checks),failed=[x for x in checks if not x['passed']],metrics=metrics),indent=2))
if out['status']!='PASS':raise SystemExit(1)
