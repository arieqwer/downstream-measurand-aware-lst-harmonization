"""Independent comparisons of regenerated results with the corrected baseline.

Run after reproduce.py, reproduce_tables.py and reproduce_figures.py. This script
does not import the scientific fit/validation functions as a reference oracle.
"""
from pathlib import Path
import os,json,hashlib,math
import numpy as np,pandas as pd
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
CASE=Path(os.environ.get('LST_REPRODUCTION_OUTPUT',str(ROOT/'outputs/reproduced'))).resolve()/'repaired'
NEW=CASE/'outputs/grl_deepening_2026';BASE=ROOT/'02_EVIDENCE/analysis_outputs'
checks=[];numcells=0
def check(name,ok,**kw):checks.append(dict(check=name,passed=bool(ok),**kw))
def compare(a,b,label):
    global numcells
    check(label+' shape',a.shape==b.shape,actual=list(a.shape),expected=list(b.shape))
    if a.shape!=b.shape:return
    check(label+' columns',list(a.columns)==list(b.columns))
    for c in a.columns.intersection(b.columns):
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
            x=a[c].to_numpy(dtype=float);y=b[c].to_numpy(dtype=float)
            good=np.allclose(x,y,atol=1e-10,rtol=1e-10,equal_nan=True)
            finite=np.isfinite(x)&np.isfinite(y)
            check(label+' column '+c,good,max_abs_difference=float(np.max(np.abs(x[finite]-y[finite]))) if finite.any() else 0.)
            numcells+=len(x)
        elif not any(z in c.lower() for z in ['path','sha256','time_utc','timestamp']):
            check(label+' labels '+c,a[c].fillna('').astype(str).equals(b[c].fillna('').astype(str)))

csvfiles=[]
for old in BASE.rglob('*.csv'):
    new=NEW/old.relative_to(BASE)
    if not new.exists():continue
    compare(pd.read_csv(new),pd.read_csv(old),'CSV '+str(old.relative_to(BASE)))
    csvfiles.append(str(old.relative_to(BASE)))
predictions=[]
for old in BASE.rglob('*.parquet'):
    new=NEW/old.relative_to(BASE)
    if not new.exists():continue
    compare(pd.read_parquet(new),pd.read_parquet(old),'PARQUET '+str(old.relative_to(BASE)))
    predictions.append(str(old.relative_to(BASE)))
for name in ['model_selection_summary.csv','uncertainty_gate_2026_by_cohort_event.csv','cohort_attrition_summary.csv','cohort_event_analysis_counts.csv']:
    compare(pd.read_csv(CASE/'si_tables'/name),pd.read_csv(ROOT/'02_EVIDENCE/si_tables'/name),'TABLE '+name)

# Independently reconstruct the population covariance identity and hour partition.
p=NEW/'goes17_goes16_external_metric/validation_2021_hourly_predictions.parquet'
f=pd.read_parquet(p)
cov=lambda a,b:float(np.mean((a-np.mean(a))*(b-np.mean(b))))
a=f.source_core.to_numpy()-f.target_core.to_numpy();b=f.source_ring.to_numpy()-f.target_ring.to_numpy()
c=f.pred_core.to_numpy()-f.target_core.to_numpy();d=f.pred_ring.to_numpy()-f.target_ring.to_numpy()
net=float(np.mean((a-b)**2)-np.mean((c-d)**2))
vg=cov(a,a)+cov(b,b)-cov(c,c)-cov(d,d)
bg=float((a.mean()-b.mean())**2-(c.mean()-d.mean())**2);penalty=2*(cov(a,b)-cov(c,d))
check('Independent MSE closure 2021',abs(vg+bg-penalty-net)<1e-12,net=net,variance_gain=vg,bias_gain=bg,covariance_penalty=penalty)
mom=[]
for _,g in f.groupby('target_hour_from_sunset'):
    ar=g.source_core.to_numpy()-g.target_core.to_numpy();br=g.source_ring.to_numpy()-g.target_ring.to_numpy()
    cr=g.pred_core.to_numpy()-g.target_core.to_numpy();dr=g.pred_ring.to_numpy()-g.target_ring.to_numpy()
    mom.append((len(g),ar.mean(),br.mean(),cr.mean(),dr.mean(),cov(ar,br),cov(cr,dr)))
m=np.asarray(mom);w=m[:,0]/m[:,0].sum()
within_raw=float(w@m[:,5]);within_corr=float(w@m[:,6])
between_raw=float(np.sum(w*(m[:,1]-a.mean())*(m[:,2]-b.mean())))
between_corr=float(np.sum(w*(m[:,3]-c.mean())*(m[:,4]-d.mean())))
check('Hour offsets preserve within-hour covariance',abs(within_raw-within_corr)<1e-12,within_raw=within_raw,within_corrected=within_corr)
check('Total covariance partitions independently',abs(within_raw+between_raw-cov(a,b))<1e-12 and abs(within_corr+between_corr-cov(c,d))<1e-12,between_raw=between_raw,between_corrected=between_corr,raw_correlation=float(np.corrcoef(a,b)[0,1]),corrected_correlation=float(np.corrcoef(c,d)[0,1]))

# Negative controls identify stale counts or a non-closing budget; these must fail.
check('Negative control rejects stale 2026 count',5744!=len(pd.read_parquet(NEW/'goes18_goes19_metric_harmonization/validation_2026_hourly_predictions.parquet')))
check('Negative control detects altered covariance sign',abs(vg+bg+penalty-net)>1)
for scope in ['hourly','transition']:
    allbud=pd.read_csv(NEW/'downstream_metric_framework/exact_mse_budgets_with_external.csv')
    g=allbud[allbud.scope.eq(scope)]
    check('All '+scope+' budget identities',np.max(np.abs(g.component_variance_gain_k2+g.differential_bias_gain_k2-g.covariance_loss_penalty_k2-g.net_downstream_mse_gain_k2))<1e-10)

figures=[]
for name in ['Figure_1_corrected_workflow_domain_chronology','Figure_2_repaired_model_selection','Figure_3_repaired_cross_platform_budget','Figure_4_repaired_covariance_regimes','Figure_5_repaired_replication_and_temporal_evaluation','Phoenix_LST_corrected_local_date']:
    new=CASE/'figures'/(name+'.png');old=ROOT/'outputs/figures'/(name+'.png')
    x=np.asarray(Image.open(new).convert('RGB'));y=np.asarray(Image.open(old).convert('RGB'))
    exact=x.shape==y.shape and np.array_equal(x,y)
    check('Figure source regeneration '+name,exact,new_shape=list(x.shape),baseline_shape=list(y.shape),pixel_identical=exact)
    figures.append(dict(name=name,pixel_identical=exact,new_sha256=hashlib.sha256(new.read_bytes()).hexdigest(),baseline_sha256=hashlib.sha256(old.read_bytes()).hexdigest()))

result=dict(status='PASS' if all(c['passed'] for c in checks) else 'FAIL',checks=len(checks),numerical_cells_compared=numcells,
            compared_csv_files=csvfiles,compared_parquet_files=predictions,figures=figures,
            assertions=checks,failed=[c for c in checks if not c['passed']],
            scope=['Full processed-input fit/selection/evaluation/bootstrap/budget recomputation under unchanged protocol.',
                   'Figures 2–5 use regenerated numerical outputs; Figure1 uses archived fixed metadata/basemaps; Figure6 uses archived decoded native arrays.',
                   'Provider raw re-extraction, new cloud/radiometry source downloads and complete urban ground validation are not asserted by this check.'])
(CASE/'reproduction_verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ['assertions','compared_csv_files','compared_parquet_files','figures']},indent=2))
if result['status']!='PASS':raise SystemExit(1)
