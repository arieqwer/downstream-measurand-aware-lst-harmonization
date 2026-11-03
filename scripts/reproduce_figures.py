"""Regenerate all six main figures from current computational outputs/assets.

Figures 2–5 use newly recomputed numerical results. Figure 1 uses retained fixed
design metadata/basemaps; Figure 6 uses retained decoded native map arrays.
Provider raw decoding is intentionally a separate reproduction level.
"""
from pathlib import Path
from datetime import datetime,timezone
import os,sys,json,hashlib
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'figure_builders'))
import traced_figure1_corrected_labels as design
import traced_figure_builder as fig
import traced_stress_figure_builder as stress
import traced_replication_figure_builder as rep
from final_figure_layout import export_fixed, style_wide_replication

CASE=Path(os.environ.get('LST_REPRODUCTION_OUTPUT',str(ROOT/'outputs/reproduced'))).resolve()/'repaired'
SCI=CASE/'outputs/grl_deepening_2026'
OUT=CASE/'figures';OUT.mkdir(parents=True,exist_ok=True)
sources={}
def record(p):sources[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()

design.OUT=OUT
design.FIXED_EXPORT_TIME=datetime(2026,11,2,tzinfo=timezone.utc)
design.BASEMAP={k:ROOT/'data/basemap'/v.name for k,v in design.BASEMAP.items()}
city=ROOT/'evidence/si_tables/fixed_city_candidate_metadata.csv'
time=ROOT/'evidence/si_tables/fixed_interval_chronology.csv'
design.export_figure(design.build_figure1(pd.read_csv(city),pd.read_csv(time)),'figure_1_corrected_workflow_domain_chronology')
record(city);record(time)
for p in design.BASEMAP.values():record(p)

fig.OUT=OUT
fig.SOURCES.update(model_selection=CASE/'si_tables/model_selection_summary.csv',
                   rmse=CASE/'tables/downstream_metric_framework_figure_rmse_source.csv',
                   mse=CASE/'tables/downstream_metric_framework_figure_budget_source.csv')
selection=pd.read_csv(fig.SOURCES['model_selection']);rmse,mse=fig.load_figure3_sources()
assert mse.budget_closure_residual_k2.abs().max()<1e-10
f2=fig.build_figure2(selection)
fig.export_figure(f2,'figure_2_repaired_model_selection');plt.close(f2)
f3=fig.build_figure3(rmse,mse)
export_fixed(f3,OUT,'figure_3_repaired_cross_platform_budget');plt.close(f3)
for p in fig.SOURCES.values():
    if p.exists():record(p)

plt.rcdefaults()
stress.FIGURES=OUT
stress.POINT_BUDGETS=SCI/'downstream_metric_framework/exact_mse_budgets_with_external.csv'
# Re-enumerate the deterministic grid rather than only loading retained values.
regimes,summary=stress.enumerate_regimes()
regimes.to_csv(OUT/'covariance_regime_grid.csv',index=False)
regimes=pd.read_csv(OUT/'covariance_regime_grid.csv')
(OUT/'covariance_regime_simulation_summary.json').write_text(json.dumps(summary,indent=2))
empirical=stress.empirical_positions();checks=stress.validate_outputs(regimes,empirical,summary)
stress.build_figure(regimes,empirical)

rep.FIGURES=OUT;rep.configure_style()
EXT=SCI/'goes17_goes16_external_metric';F=SCI/'downstream_metric_framework'
points=pd.read_csv(EXT/'validation_2021_exact_mse_budget.csv')
ci=pd.read_csv(EXT/'validation_2021_bootstrap_summary.csv')
events=pd.read_csv(EXT/'validation_2021_event_influence.csv')
intervals=pd.read_csv(ROOT/'data/corrected_inputs/goes17_2019_2021_external_metric/goes_sunset_intervals.csv').rename(columns={'time_id':'event_time_id'})
single=events[events.diagnostic.eq('single_event')].merge(intervals[['event_time_id','start_date','analysis_role']],on='event_time_id',validate='one_to_one').sort_values('start_date')
budgets=pd.read_csv(F/'exact_mse_budgets_with_external.csv')
mp=budgets[budgets.scope.eq('hourly')&budgets['sample'].eq('2026 combined GOES18/19')]
mc=pd.read_csv(F/'mse_budget_2026_bootstrap_summary.csv')
mc=mc[mc.scope.eq('hourly')&mc.metric.isin(['component_variance_gain_k2','differential_bias_gain_k2','covariance_loss_penalty_k2','net_downstream_mse_gain_k2'])]
gate=pd.read_csv(CASE/'si_tables/uncertainty_gate_2026_by_cohort_event.csv');gate=gate[gate.scope_type.eq('cohort')]
data=dict(external_point=points[points.scope.eq('hourly')],
          external_ci=ci[ci.scope.eq('hourly')&ci.metric.isin(['core_rmse_reduction_fraction','ring_rmse_reduction_fraction','anomaly_rmse_reduction_fraction'])],
          single_events=single,mse_point=mp,mse_ci=mc,gate_cohorts=gate)
f=rep.build_figure4(data);baseline=rep.build_figure4(data)
style_wide_replication(f,baseline,gate,rep)
export_fixed(f,OUT,'figure_5_repaired_replication_and_temporal_evaluation',900)
plt.close(f);plt.close(baseline)

# Native spatial-map arrays retain the precise grids and screening of the study.
plt.rcdefaults()
from shapely.geometry import shape
from matplotlib.colors import Normalize
M=ROOT/'data/map_arrays'
scenes=[s for s in json.loads((M/'cloud8_audit_summary.json').read_text())['files'] if s['local_date']=='2026-06-01']
scenes.sort(key=lambda s:(s['target_hour'],s['bucket']));assert len(scenes)==4
g=json.loads((ROOT/'data/corrected_inputs/goes18_2026_metric_holdout/goes_city_units.geojson').read_text())
geoms={(str(x['properties']['uc_id']),x['properties']['unit']):shape(x['geometry']) for x in g['features']}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':9.5,'axes.labelsize':9,
                     'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'lst-figure6-nov2'})
f,axs=plt.subplots(2,2,figsize=(8,7),sharex=True,sharey=True,layout='constrained');scale=Normalize(240,330)
for ax,s,letter in zip(axs.flat,scenes,'abcd'):
    p=M/(s['label']+'_map_arrays.npz').lower();a=np.load(p);record(p)
    lo,la,v=a['lon'],a['lat'],a['lst']
    valid=np.isfinite(v)&(lo>=-113)&(lo<=-111.4)&(la>=32.9)&(la<=34.3)
    assert valid.any() and v[valid].min()>=240 and v[valid].max()<=330
    start=pd.Timestamp(s['global']['time_coverage_start']);sunset=pd.Timestamp(s['sunset_utc'])
    actual=(start-sunset).total_seconds()/3600
    mesh=ax.pcolormesh(lo,la,v,shading='nearest',cmap='inferno',norm=scale,rasterized=True)
    for unit,style in [('core','-'),('ring','--')]:
        geom=geoms[('4699',unit)];parts=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
        for part in parts:
            x,y=part.exterior.xy;ax.plot(x,y,style,c='#006400',lw=.95)
            for hole in part.interiors:x,y=hole.xy;ax.plot(x,y,style,c='#006400',lw=.95)
    np.testing.assert_array_equal(np.ma.filled(mesh.get_array(),np.nan).reshape(v.shape),v)
    role='GOES-18 reference' if s['bucket']=='noaa-goes18' else 'GOES-19 source'
    ax.set_title(f'{role} | target h={s["target_hour"]:+d}, actual {actual:+.2f} h\n{start.strftime("%Y-%m-%d %H:%M:%S")} UTC')
    ax.set_xlim(-113,-111.4);ax.set_ylim(32.9,34.3);ax.set_aspect(1/np.cos(np.radians(33.6)))
    ax.set_xlabel('Longitude (°E)');ax.set_ylabel('Latitude (°N)');ax.grid(c='.8',lw=.4,alpha=.4)
    ax.text(-.26,1.16,letter,transform=ax.transAxes,ha='left',va='top',fontsize=12,fontweight='bold',color='black',clip_on=False)
f.colorbar(mesh,ax=axs,label='Native recommended-quality land surface temperature (K)',shrink=.85)
f.suptitle('Phoenix: urban core and surrounding 10–20 km ring\nLocal sunset date: 1 June 2026',fontsize=11)
export_fixed(f,OUT,'phoenix_lst_corrected_local_date',600)
plt.close(f)
(OUT/'reproduction_sources.json').write_text(json.dumps(dict(sources=sources,stress_checks=checks,scope='Figs2–5 use recomputed results; Fig1 fixed-design sources; Fig6 retained decoded native arrays'),indent=2))
print('ALL_SIX_FIGURES_REGENERATED',OUT)
