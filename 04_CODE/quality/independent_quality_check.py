"""Read-only independent checks. Does not import the candidate rerun functions."""
from pathlib import Path
import os
PACKAGE_ROOT=Path(__file__).resolve().parents[2]
NATIVE_WORKSPACE=Path(os.environ.get("LST_NATIVE_WORKSPACE",str(PACKAGE_ROOT/"data/native_workspace"))).resolve()
import json,hashlib
import numpy as np,pandas as pd
B=NATIVE_WORKSPACE/'auxiliary/quality';R=B/'results'
manifest=json.loads((R/'validation_manifest.json').read_text());budgets=pd.read_csv(R/'full_mse_decompositions.csv');support=pd.read_csv(R/'support_summary.csv')
checks=[]
for scenario in support.scenario:
 for level in ['hourly','transition']:
  f=pd.read_parquet(R/f'{scenario}_{level}.parquet');e=np.vstack([(f.source_core-f.target_core).values,(f.source_ring-f.target_ring).values,(f.pred_core-f.target_core).values,(f.pred_ring-f.target_ring).values]);means=np.mean(e,axis=1);cov=np.cov(e,bias=True)
  direct=np.mean((e[0]-e[1])**2)-np.mean((e[2]-e[3])**2)
  vg=cov[0,0]+cov[1,1]-cov[2,2]-cov[3,3];bg=(means[0]-means[1])**2-(means[2]-means[3])**2;pen=2*(cov[0,1]-cov[2,3])
  row=budgets[budgets.scenario.eq(scenario)&budgets.level.eq(level)].iloc[0]
  err=max(abs(direct-row.net_contrast_mse_gain_K2),abs(vg-row.variance_gain_K2),abs(bg-row.differential_bias_gain_K2),abs(pen-row.covariance_loss_penalty_K2));assert err<1e-10
  checks.append(dict(scenario=scenario,level=level,n=len(f),independent_budget_max_error_K2=err))
# Independent recomputation of common strict daily means and support from the complete
# paired source table; no candidate aggregation function is imported.
p=pd.read_parquet(R/'paired_daily_regional_summaries.parquet');common=p.valid_common
recomputed={}
for role in ['reference','source']:
 for unit in ['core','ring']:
  col=f'{unit}_strict_lst_k_{role}';x=p.loc[common].groupby(['uc_id','event_year','event_step8','event_time_id','target_hour_from_sunset'])[col].mean();recomputed[(role,unit)]=x
f=pd.read_parquet(R/'strict_common_daily_hourly.parquet').set_index(['uc_id','event_year','event_step8','event_time_id','target_hour_from_sunset'])
for (role,unit),x in recomputed.items():
 expected=f[('target' if role=='reference' else 'source')+'_'+unit]
 assert len(x)==len(expected) and np.max(np.abs(x.sort_index().values-expected.sort_index().values))<1e-12
expected=support[support.scenario.eq('strict_common_daily')].iloc[0];assert len(f)==expected.hourly_rows and f.reset_index().uc_id.nunique()==expected.cities
# All cell-weight bootstrap records and paired differences are finite; quantiles agree.
draw=pd.read_parquet(R/'paired_crossed_bootstrap_draws.parquet');delta=pd.read_parquet(R/'paired_crossed_bootstrap_differences.parquet');ds=pd.read_csv(R/'paired_crossed_bootstrap_comparison_summary.csv')
assert draw.groupby(['level','scenario']).size().eq(5000).all();assert delta.groupby(['level','comparison']).size().eq(5000).all()
assert np.isfinite(draw.select_dtypes('number')).all().all()
for row in ds.itertuples():
 v=delta.loc[delta.level.eq(row.level)&delta.comparison.eq(row.comparison),row.metric].values;q=np.percentile(v,[2.5,97.5]);assert max(abs(q[0]-row.lower_95),abs(q[1]-row.upper_95))<1e-10
for item in manifest['inputs'].values():assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']
result=dict(independent_checks=checks,common_strict_daily_reaggregation_pass=True,paired_bootstrap_draw_counts_and_quantiles_pass=True,source_input_hashes_unchanged=True,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),note='Independent implementation uses direct error vectors and numpy.cov rather than candidate sufficient-statistic functions; no models fitted or Word edits.')
(R/'independent_quality_check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
