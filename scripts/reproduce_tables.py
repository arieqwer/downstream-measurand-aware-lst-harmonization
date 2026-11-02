from pathlib import Path
import os,json,shutil
import numpy as np,pandas as pd
import build_si_evidence_tables as si
ROOT=Path(__file__).resolve().parents[1]
ARC=ROOT
CASE=Path(os.environ.get('LST_REPRODUCTION_OUTPUT',str(ROOT/'outputs/reproduced'))).resolve()/'repaired'
def transitions_count(f):
    z=f.assign(pre=f.target_hour_from_sunset.isin([-3,-2,-1]),post=f.target_hour_from_sunset.isin([4,5,6])).groupby(['uc_id','event_time_id'])[['pre','post']].sum()
    return int((z.pre.ge(2)&z.post.ge(2)).sum())

def stage_tables(case,out):
    root=case/'outputs/grl_deepening_2026'
    external=json.loads((root/'goes17_goes16_external_metric/external_replication_report.json').read_text())
    rows=[];ev=[];members={}
    for st in si.STAGES:
        if st.hourly_path:
            f=pd.read_parquet(case/st.hourly_path);f.uc_id=f.uc_id.astype(str);members[st.stage_id]=set(f.uc_id)
            t=pd.read_parquet(case/st.transition_path) if st.transition_path else None
            ntrans=len(t) if t is not None else transitions_count(f)
            ncity=f.uc_id.nunique();n=len(f);nevent=f.event_time_id.nunique()
            for eid,g in f.groupby('event_time_id'):
                ev.append(dict(stage_id=st.stage_id,event_time_id=int(eid),event_year=int(g.event_year.iloc[0]),
                               event_step8=int(g.event_step8.iloc[0]),analyzed_cities=g.uc_id.nunique(),hourly_city_event_rows=len(g),
                               eligible_transition_city_events=int((t.event_time_id==eid).sum()) if t is not None else transitions_count(g)))
        else:
            er=external[st.external_report_key];ncity=er['n_cities'];n=er.get('n_rows',er.get('n_hourly'));nevent=er['n_events'];ntrans=er.get('n_transitions')
        assert nevent==st.interval_count,(st.stage_id,nevent)
        rows.append(dict(stage_id=st.stage_id,analysis_role=st.analysis_role,reference_platform=st.reference_platform,source_platform=st.source_platform,
                         candidate_cities=st.candidate_count,analyzed_cities=ncity,excluded_cities=st.candidate_count-ncity,
                         city_retention_fraction=ncity/st.candidate_count,fixed_intervals=st.interval_count,
                         hourly_city_event_rows=n,eligible_transition_city_events=ntrans))
    pd.DataFrame(rows).to_csv(out/'cohort_attrition_summary.csv',index=False)
    attr=pd.read_csv(root/'goes17_goes16_external_metric/event_attrition.csv')
    for r in attr[attr.analysis_role.eq('calibration')].itertuples():
        ev.append(dict(stage_id='external_calibration_combined_2019_2020',event_time_id=int(r.event_time_id),event_year=int(r.event_year),
                       event_step8=int(r.event_time_id)-3000,analyzed_cities=int(r.retained_cities),hourly_city_event_rows=int(r.retained_city_event_hour_rows),
                       eligible_transition_city_events=None))
    events=pd.DataFrame(ev).sort_values(['stage_id','event_time_id']);events.to_csv(out/'cohort_event_analysis_counts.csv',index=False)
    assert events.hourly_city_event_rows.sum()==sum(x['hourly_city_event_rows'] for x in rows)
    return rows,members

def selection(root,out):
    initial=pd.read_csv(root/'multiplatform_harmonization/derivation_model_selection.csv').rename(columns={'mean_composite':'mean_cv_score','sd_composite':'sd_cv_score','se_composite':'se_cv_score'})
    initial['selection_stage']='initial_harmonization_2022_2024';initial['outcome']='hourly_composite';initial['score_name']='mean_normalized_six_outcome_rmse_ratio'
    initial['parsimony_rank']=initial.model.map({'raw':1,'hour_offset':2,'hour_spline':3,'geometry_ridge':4})
    metric=pd.read_csv(root/'goes18_goes19_metric_harmonization/model_selection.csv').rename(columns={'mean_rmse_ratio':'mean_cv_score','sd_rmse_ratio':'sd_cv_score','se_rmse_ratio':'se_cv_score'})
    metric['selection_stage']='metric_aware_calibration_2025';metric['score_name']='rmse_ratio_to_raw'
    ranks={'raw':1,'hour_offset':2,'geometry_ridge':3,'scene_gbdt':4,'mean_offset':2,'transition_ridge':3,'transition_gbdt':4}
    metric['parsimony_rank']=metric.model.map(ranks)
    f=pd.concat([initial,metric],ignore_index=True)
    f['selection_rule']='one_standard_error_with_predeclared_parsimony_order'
    assert len(f)==20
    cols=['selection_stage','outcome','model','parsimony_rank','score_name','mean_cv_score','sd_cv_score','se_cv_score','n_folds','one_se_threshold','selected','selection_rule']
    f[cols].to_csv(out/'model_selection_summary.csv',index=False)

def plotting_sources(case,root):
    out=case/'tables';out.mkdir(exist_ok=True)
    rmse=pd.read_csv(root/'downstream_metric_framework/cross_sample_rmse_with_external.csv')
    cols=pd.read_csv(ARC/'02_EVIDENCE/tables/downstream_metric_framework_figure_rmse_source.csv',nrows=0).columns.tolist()
    rmse[cols].sort_values(['sample','component']).to_csv(out/'downstream_metric_framework_figure_rmse_source.csv',index=False)
    budget=pd.read_csv(root/'downstream_metric_framework/exact_mse_budgets_with_external.csv')
    cols=pd.read_csv(ARC/'02_EVIDENCE/tables/downstream_metric_framework_figure_budget_source.csv',nrows=0).columns.tolist()
    budget.loc[budget.scope.eq('hourly'),cols].sort_values('sample').to_csv(out/'downstream_metric_framework_figure_budget_source.csv',index=False)
    shutil.copyfile(root/'downstream_metric_framework/exact_mse_budgets_with_external.csv',out/'exact_mse_budgets_with_external.csv')
if __name__=='__main__':
 out=CASE/'si_tables';out.mkdir(parents=True,exist_ok=True)
 root=CASE/'outputs/grl_deepening_2026'
 stage_tables(CASE,out);selection(root,out);plotting_sources(CASE,root)
 chronology=pd.read_csv(ROOT/'02_EVIDENCE/si_tables/fixed_interval_chronology.csv')
 si.build_uncertainty_gate(CASE,chronology).to_csv(out/'uncertainty_gate_2026_by_cohort_event.csv',index=False)
 print('REPRODUCED_CURRENT_NUMERICAL_TABLES',out)
