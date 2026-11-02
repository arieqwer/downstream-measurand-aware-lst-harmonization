from pathlib import Path
import json,hashlib,sys,platform
import numpy as np,pandas as pd

B=Path('/Users/apple/Downloads/RS revision 1');R=B/'repair_20261029';S=R/'pipeline/repaired/outputs/grl_deepening_2026';O=B/'continuation_20261029/science/claims_audit'
checks=[];sources={};results={}
def load(p):
 sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return pd.read_parquet(p) if p.suffix=='.parquet' else pd.read_csv(p)
def check(name,ok,details=None):checks.append(dict(name=name,passed=bool(ok),details=details))
def close(name,a,b,atol=1e-10):check(name,np.allclose(a,b,atol=atol,rtol=1e-11),dict(actual=np.asarray(a).tolist(),expected=np.asarray(b).tolist()))
def residuals(f,suffix=''):
 return np.column_stack([f['source_core'+suffix]-f['target_core'+suffix],f['source_ring'+suffix]-f['target_ring'+suffix],f['pred_core'+suffix]-f['target_core'+suffix],f['pred_ring'+suffix]-f['target_ring'+suffix]])
def moments(e):
 mu=e.mean(axis=0);x=e-mu;C=x.T@x/len(e);m=np.mean(e*e,axis=0)
 raw=np.mean((e[:,0]-e[:,1])**2);harm=np.mean((e[:,2]-e[:,3])**2)
 vg=C[0,0]+C[1,1]-C[2,2]-C[3,3];bg=(mu[0]-mu[1])**2-(mu[2]-mu[3])**2;cp=2*(C[0,1]-C[2,3]);gain=raw-harm
 assert abs(gain-(vg+bg-cp))<1e-10
 return dict(n=len(e),raw_core_rmse=float(np.sqrt(m[0])),raw_ring_rmse=float(np.sqrt(m[1])),corrected_core_rmse=float(np.sqrt(m[2])),corrected_ring_rmse=float(np.sqrt(m[3])),raw_contrast_rmse=float(np.sqrt(raw)),corrected_contrast_rmse=float(np.sqrt(harm)),variance_gain=float(vg),bias_gain=float(bg),covariance_penalty=float(cp),net_MSE_gain=float(gain),raw_covariance=float(C[0,1]),corrected_covariance=float(C[2,3]),raw_correlation=float(C[0,1]/np.sqrt(C[0,0]*C[1,1])),corrected_correlation=float(C[2,3]/np.sqrt(C[2,2]*C[3,3])))

h21=load(S/'goes17_goes16_external_metric/validation_2021_hourly_predictions.parquet');h26=load(S/'goes18_goes19_metric_harmonization/validation_2026_hourly_predictions.parquet');t26=load(S/'goes18_goes19_metric_harmonization/validation_2026_transition_predictions.parquet');cv=load(S/'goes18_goes19_metric_harmonization/transition_cross_validated_predictions.parquet')
keys=['uc_id','event_time_id','target_hour_from_sunset']
check('Unique hourly keys',not h21.duplicated(keys).any() and not h26.duplicated(keys).any())
point={}
for label,f,suffix in [('2021 hourly',h21,''),('2026 hourly',h26,''),('2026 transition',t26,'_transition')]:
 point[label]=moments(residuals(f,suffix))
check('2021/2026 supports',len(h21)==2602 and h21.uc_id.nunique()==69 and len(h26)==5716 and h26.uc_id.nunique()==75 and len(t26)==583)
bud=load(S/'downstream_metric_framework/exact_mse_budgets_with_external.csv')
for label,year,scope in [('2021 hourly','2021 external GOES17/16','hourly'),('2026 hourly','2026 combined GOES18/19','hourly'),('2026 transition','2026 combined GOES18/19','transition')]:
 row=bud[bud['sample'].eq(year)&bud.scope.eq(scope)].iloc[0];p=point[label]
 close(label+' independent budget',[p['variance_gain'],p['bias_gain'],p['covariance_penalty'],p['net_MSE_gain']],[row.component_variance_gain_k2,row.differential_bias_gain_k2,row.covariance_loss_penalty_k2,row.net_downstream_mse_gain_k2])

# Independent law-of-total-covariance calculation via explicit centered vectors.
e=residuals(h21);n=len(e);hour=h21.target_hour_from_sunset.to_numpy();means=[];weights=[];within=np.zeros((4,4));hourrows=[]
for h in sorted(np.unique(hour)):
 z=e[hour==h];mu=z.mean(axis=0);w=len(z)/n;C=(z-mu).T@(z-mu)/len(z);within+=w*C;means.append(mu);weights.append(w)
 close('2021 h'+str(h)+' centered covariance invariant',C[0,1],C[2,3])
 close('2021 h'+str(h)+' correction is offset',np.ptp(z[:,2]-z[:,0]),0)
 close('2021 h'+str(h)+' ring correction is offset',np.ptp(z[:,3]-z[:,1]),0)
 row=moments(z);row['h']=int(h);hourrows.append(row)
means=np.array(means);weights=np.array(weights);grand=weights@means;between=((means-grand)*weights[:,None]).T@(means-grand)
total=(e-e.mean(axis=0)).T@(e-e.mean(axis=0))/n
close('Total covariance closes',within+between,total)
results['historical_covariance_partition']={k:dict(raw=float(C[0,1]),corrected=float(C[2,3])) for k,C in [('within',within),('between',between),('total',total)]}
check('Every historical hourly contrast improves',all(x['corrected_contrast_rmse']<x['raw_contrast_rmse'] for x in hourrows))
off=load(R/'pipeline/repaired/si_tables/external_hour_offsets_2019_2020.csv')
results['historical_differential_offsets']=[dict(h=int(x.target_hour_from_sunset),differential_offset=float(x.core_offset_k-x.ring_offset_k)) for x in off.itertuples()]
close('h-3 offset difference',[x['differential_offset'] for x in results['historical_differential_offsets'] if x['h']==-3][0],.5883857535349724)
for h in sorted(h26.target_hour_from_sunset.unique()):
 f=h26[h26.target_hour_from_sunset.eq(h)]
check('2026 geometry correction varies within hour',any(np.ptp((h26.loc[h26.target_hour_from_sunset.eq(h),'pred_core']-h26.loc[h26.target_hour_from_sunset.eq(h),'source_core']).to_numpy())>1e-3 for h in h26.target_hour_from_sunset.unique()))
point['2021 June only']=moments(residuals(h21[h21.event_time_id.isin([3005,3006])]))
point['2021 July only']=moments(residuals(h21[h21.event_time_id.isin([3007,3008])]))
check('June sensitivity support',point['2021 June only']['n']==1330)

# Radius reconstructed from corrected 2025 OOF raw residuals, with no model load.
rawcv=cv[cv.model.eq('raw')];check('OOF raw 2025 transition support',len(rawcv)==737 and not rawcv.duplicated(['uc_id','event_time_id']).any())
# The fixed original training implementation explicitly uses interpolation=higher.
# The initial independent default-linear attempt is retained, including its failed
# comparison. This alignment does not alter the source radius or any fitted value.
radius=float(np.quantile(abs(rawcv.estimate-rawcv.target),.9,method='higher'));source=t26.source_anomaly_transition.to_numpy();target=t26.target_anomaly_transition.to_numpy()
check('Negative control default-linear quantile rejected',not np.isclose(float(np.quantile(abs(rawcv.estimate-rawcv.target),.9)),radius,rtol=0,atol=1e-10))
close('Interval radius equals OOF 90th percentile',t26.prediction_high-t26.direct_transition_prediction,radius)
close('Direct action remains raw',source,t26.direct_transition_prediction)
cover=np.abs(source-target)<=radius;sg=np.where(source-radius>0,1,np.where(source+radius<0,-1,0));correct=(sg==np.sign(target))&(sg!=0)
gate=[]
for label,mask in [('combined',np.ones(len(t26),bool)),('original',t26.calibration_cohort.eq('original').to_numpy()),('expansion',t26.calibration_cohort.eq('expansion').to_numpy())]:
 n=int(mask.sum());ns=int(((sg!=0)&mask).sum());nc=int((correct&mask).sum());c=int((cover&mask).sum())
 gate.append(dict(cohort=label,n=n,covered_n=c,coverage=c/n,supported_n=ns,support_fraction=ns/n,matching_supported_n=nc,agreement=nc/ns,coverage_in_band=.85<=c/n<=.95,agreement_at_least90=nc/ns>=.9))
close('Stored interval coverage matches independent decisions',cover,t26.covered.to_numpy())
close('Stored supported signs match independent decisions',sg,t26.certified_sign.to_numpy())
check('Pooled pass, expansion both fail, original overcovers',gate[0]['coverage_in_band'] and gate[0]['agreement_at_least90'] and not gate[2]['coverage_in_band'] and not gate[2]['agreement_at_least90'] and gate[1]['coverage']>.95)
results['radius_K']=radius;results['directional']=gate
for year,f in [(2021,h21),(2026,h26)]:
 absref=abs(f.target_core-f.target_ring).to_numpy();results[str(year)+'_contrast_scale']=dict(median_signed=float(np.median(f.target_core-f.target_ring)),median_absolute=float(np.median(absref)),iqr=np.quantile(absref,[.25,.75]).tolist(),fraction_below1K=float(np.mean(absref<1)),raw_RMSE_over_median_abs=point[str(year)+' hourly']['raw_contrast_rmse']/np.median(absref))
results['2026_VZA_ranges']=dict(reference=[float(h26.vza_target.min()),float(h26.vza_target.max())],source=[float(h26.vza_source.min()),float(h26.vza_source.max())])
results['2026_VZA_reference_strata']=[dict(lo=lo,hi=hi,**moments(residuals(h26[h26.vza_target.ge(lo)&h26.vza_target.lt(hi)]))) for lo,hi in [(40,50),(50,60)]]

# Recreate daily quality eligibility from paired regional extraction, independently
# of the stored booleans, and then means/transition keys without model application.
Q=R/'auxiliary/quality/results';p=load(Q/'paired_daily_regional_summaries.parquet');gap=(pd.to_datetime(p.scan_time_utc_reference,utc=True,format='mixed')-pd.to_datetime(p.scan_time_utc_source,utc=True,format='mixed')).dt.total_seconds().abs()/60
valids={}
for qa in ['recommended','strict']:
 valid=gap.lt(1)
 for side in ['reference','source']:
  for unit,minimum in [('core',3),('ring',10)]:valid &= p[f'{unit}_{qa}_count_{side}'].ge(minimum)&p[f'{unit}_{qa}_lst_k_{side}'].between(180,380)
 valids[qa]=valid
 check(qa+' eligibility independently reconstructed <1minute',np.array_equal(valid,p['valid_'+qa]))
common=valids['recommended']&valids['strict'];check('Common daily flags match',np.array_equal(common,p.valid_common))
dailykeys=['uc_id','event_year','event_step8','event_time_id','target_hour_from_sunset','local_date'];group=dailykeys[:-1]
check('No repeated daily keys',not p.duplicated(dailykeys).any())
qrows=[]
for name,qa,keep in [('recommended_full','recommended',valids['recommended']),('strict_full','strict',valids['strict']),('recommended_common_daily','recommended',common),('strict_common_daily','strict',common)]:
 z=p[keep];agg=z.groupby(group).agg(**{f'{out}_{u}':(f'{u}_{qa}_lst_k_{side}','mean') for out,side in [('source','source'),('target','reference')] for u in ['core','ring']}).reset_index();actual=load(Q/(name+'_hourly.parquet'));t=load(Q/(name+'_transition.parquet'))
 merged=agg.merge(actual,on=group,validate='one_to_one',suffixes=('_computed','_retained'));check(name+' hourly support',len(merged)==len(actual))
 for c in ['source_core','source_ring','target_core','target_ring']:close(name+' '+c,merged[c+'_computed'],merged[c+'_retained'])
 pre=agg[agg.target_hour_from_sunset.isin([-3,-2,-1])].groupby(group[:-1]).target_hour_from_sunset.nunique();post=agg[agg.target_hour_from_sunset.isin([4,5,6])].groupby(group[:-1]).target_hour_from_sunset.nunique();eligible=pre[pre>=2].index.intersection(post[post>=2].index)
 check(name+' transition support',len(t)==len(eligible))
 qrows.append(dict(scenario=name,paired_daily_n=int(keep.sum()),hourly_n=len(actual),transition_n=len(t),city_ids=sorted(str(x) for x in actual.uc_id.unique()),hourly=moments(residuals(actual)),transition=moments(residuals(t))))
results['quality_support']=qrows
check('Strict support 3cities215hourly21transitions883daily',qrows[1]['hourly_n']==215 and qrows[1]['transition_n']==21 and qrows[1]['paired_daily_n']==883 and len(qrows[1]['city_ids'])==3)
strict=load(Q/'strict_common_daily_hourly.parquet');recomm=load(Q/'recommended_common_daily_hourly.parquet')
check('Identical strict/recommended common hourly keys',strict[group].equals(recomm[group]))
results['strict_quality_geography']=strict[['uc_id','lat','lon','vza_target','vza_source']].drop_duplicates().to_dict('records')
results['quality_max_daily_gap_minutes']=float(gap[valids['recommended']].max())

# Cloud acquisition-level metrics recomputed from observation vectors, with exact
# shared keys and unmodified stage-specific predictions.
C=R/'auxiliary/native/cloud8/results';cloud=load(C/'native_cloud_paired_rows.csv');cloudsumm=load(C/'native_cloud_sensitivity.csv');cloudkeys=['uc_id','event_year','event_step8','event_time_id','local_date','target_hour_from_sunset']
crows=[]
for row in cloudsumm.itertuples():
 f=cloud[cloud.screen.eq(row.screen)&cloud.eligible].copy()
 if row.support.startswith('matched_to_'):
  screen=row.support[len('matched_to_'):];shared=cloud[cloud.screen.eq(screen)&cloud.eligible][cloudkeys]
  f=f.merge(shared,on=cloudkeys,validate='one_to_one')
 check('Cloud unique keys '+row.screen+'/'+row.support,not f.duplicated(cloudkeys).any())
 pnt=moments(residuals(f));close('Cloud contrast RMSE '+row.screen+'/'+row.support,[pnt['raw_contrast_rmse'],pnt['corrected_contrast_rmse']],[row.contrast_rmse_raw,row.contrast_rmse_corrected])
 close('Cloud MSE gain '+row.screen+'/'+row.support,pnt['net_MSE_gain'],row.net_contrast_MSE_gain)
 check('Cloud counts '+row.screen+'/'+row.support,len(f)==row.n and f.uc_id.nunique()==row.cities and f.local_date.nunique()==8)
 crows.append(dict(screen=row.screen,support=row.support,n=len(f),cities=f.uc_id.nunique(),days=f.local_date.nunique(),raw_contrast_rmse=pnt['raw_contrast_rmse'],corrected_contrast_rmse=pnt['corrected_contrast_rmse'],net_gain=pnt['net_MSE_gain']))
results['cloud']=crows
selection=json.loads((R/'auxiliary/native/results/cloud8_selection_predeclared.json').read_text());sources[str(R/'auxiliary/native/results/cloud8_selection_predeclared.json')]=hashlib.sha256((R/'auxiliary/native/results/cloud8_selection_predeclared.json').read_bytes()).hexdigest()
records=selection['records'];check('32 selected platform acquisitions',len(records)==32)
check('Eight local dates and two Phoenix target hours',len({x['local_date'] for x in records})==8 and {x['target_hour'] for x in records}=={-3,4})
results['cloud_selection']=dict(local_dates=sorted({x['local_date'] for x in records}),n_platform_acquisitions=len(records),target_hours=sorted({x['target_hour'] for x in records}))
dates_by_event={int(x['event_time_id']):x['local_date'] for x in records};intervals=load(R/'pipeline/repaired/si_tables/fixed_interval_chronology.csv')
results['chronology_columns']=list(intervals)
for e,date in dates_by_event.items():
 selected=intervals[intervals.event_time_id.eq(e)]
 check('Cloud first local date interval'+str(e),len(selected)>0 and all(str(x)==date for x in selected.start_date))

# Deterministic controls: additive common shifts alter pooled hour structure but
# cannot alter within-hour centered covariance; zero-excluding intervals abstain.
z=np.array([[1.,3.,4.,4.],[2.,5.,5.,6.],[3.,7.,6.,8.]])
close('Control constant-offset centered covariance',np.cov(z[:,0],z[:,1],bias=True)[0,1],np.cov(z[:,2],z[:,3],bias=True)[0,1])
testsource=np.array([-2.,0.,2.]);rad=1.;signed=np.where(testsource-rad>0,1,np.where(testsource+rad<0,-1,0));check('Control signs abstain within radius',np.array_equal(signed,[-1,0,1]))
check('Negative control stale 5744 count rejected',len(h26)!=5744)
results['point_estimates']=point;results['historical_hourly']=hourrows
check('All read inputs immutable',all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in sources.items()))
out=dict(status='PASS' if all(x['passed'] for x in checks) else 'FAIL',command='/usr/bin/python3 '+str(Path(__file__).resolve()),environment=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),checks=checks,results=results,input_hashes=sources,limitations=['This audit independently regenerates scalar calculations from corrected per-observation predictions and daily regional extracts. It does not re-extract provider raw NetCDF grids or refit models.','Cloud metrics are recomputed from retained processed scene rows; native pixel masking is inspected in source code and not re-executed here.','No full LHP causal attribution, ABI retrieval-input perturbation or urban ground validation is claimed.'])
(O/'independent_claims_results.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(status=out['status'],checks=len(checks),failed=[x for x in checks if not x['passed']],results=results),indent=2))
if out['status']!='PASS':raise SystemExit(1)
