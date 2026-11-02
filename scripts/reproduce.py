"""Run archived scientific functions with explicit isolated paths.

No original script, raw input, or frozen model is overwritten. Candidate families,
fit/selection functions, splits, support rules, and seeds are imported unchanged.
"""
from pathlib import Path
import argparse,contextlib,copy,hashlib,importlib,json,os,sys,time,traceback
import numpy as np,pandas as pd,joblib,h5py,requests

PACKAGE_ROOT=Path(__file__).resolve().parents[1]
B=Path(os.environ.get('LST_REPRODUCTION_OUTPUT',str(PACKAGE_ROOT/'outputs/reproduced'))).resolve()
E=PACKAGE_ROOT/'data'
SCI=PACKAGE_ROOT
ARC=PACKAGE_ROOT/'scripts'
sys.path[:0]=[str(ARC),str(SCI/'scripts')]
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')

names=['run_multiplatform_replication_audit','run_multiplatform_harmonization',
       'run_expanded_harmonization_validation','train_goes18_goes19_metric_harmonization',
       'validate_goes18_goes19_metric_harmonization_2026','run_goes17_goes16_external_metric_replication',
       'analyze_harmonization_error_cascade','analyze_downstream_metric_framework',
       'synthesize_downstream_metric_framework']
M={n:importlib.import_module(n) for n in names}
ra=M[names[0]];h=M[names[1]];ex=M[names[2]];tr=M[names[3]];va=M[names[4]];ext=M[names[5]];cas=M[names[6]];bud=M[names[7]];syn=M[names[8]]
old_defs=copy.deepcopy(ra.PAIR_DEFINITIONS);old_exp=copy.deepcopy(ex.DEFINITIONS)
DATASETS=['goes18_2022_2024_same_sensor','goes16_2018_2024_full_census',
          'goes18_2025_western_replication','goes19_2025_holdout',
          'goes18_2022_2024_expansion','goes16_2018_2024_low_green',
          'goes18_2025_expansion','goes19_2025_low_green']
OUTNAMES={'goes16_2018_2024_full_census':'goes16_2018_2024_full_census',
          'goes16_2018_2024_low_green':'goes16_2018_2024_low_green',
          **{k:k for k in DATASETS}}

def sha(p):
    z=hashlib.sha256()
    with Path(p).open('rb') as f:
        for q in iter(lambda:f.read(1024*1024),b''):z.update(q)
    return z.hexdigest()

def protocol(name):return SCI/'03_PROTOCOLS'/name

def configure(mode):
    case=B/mode;out=case/'outputs/grl_deepening_2026';data=SCI/'data' if mode=='baseline' else E/'corrected_inputs'
    def mapped(p):
        p=Path(p)
        if '/outputs/' in str(p):
            if mode=='baseline':return SCI/'outputs'/str(p).split('/outputs/',1)[1]
            return case/'outputs'/str(p).split('/outputs/',1)[1]
        if '/data/' in str(p):return data/str(p).split('/data/',1)[1]
        return p
    defs=copy.deepcopy(old_defs);expanded=copy.deepcopy(old_exp)
    for d in [*defs,*expanded.values()]:
        for k in ['hourly_a','hourly_b','metrics_a','metrics_b','cities']:
            if k in d:d[k]=mapped(d[k])
    ra.OUT=out/'multiplatform_replication_audit';ra.PAIR_DEFINITIONS=defs
    h.ROOT=case;h.OUT=out/'multiplatform_harmonization';h.PAIR_DEFINITIONS=defs
    h.PROTOCOL=protocol('MULTIPLATFORM_HARMONIZATION_PROTOCOL.md')
    h.MODEL_PATH=h.OUT/'frozen_harmonization_model.joblib';h.MANIFEST_PATH=h.OUT/'frozen_harmonization_manifest.json'
    ex.ROOT=case;ex.OUT=out/'multiplatform_expanded_validation';ex.BASE_OUT=h.OUT;ex.MODEL_PATH=h.MODEL_PATH;ex.DEFINITIONS=expanded
    tr.ROOT=case;tr.OUT=out/'goes18_goes19_metric_harmonization';tr.SOURCE=ex.OUT/'combined_2025_common_domain_predictions.parquet'
    tr.PROTOCOL=protocol('GOES18_GOES19_METRIC_AWARE_HARMONIZATION_PROTOCOL.md');tr.MODEL_PATH=tr.OUT/'frozen_metric_aware_model.joblib'
    va.ROOT=case;va.OUT=tr.OUT;va.MODEL_PATH=tr.MODEL_PATH;va.DATA18=data/'goes18_2026_metric_holdout';va.DATA19=data/'goes19_2026_metric_holdout'
    ext.ROOT=case;ext.OUT=out/'goes17_goes16_external_metric';ext.DATA16=data/'goes16_2019_2021_external_metric';ext.DATA17=data/'goes17_2019_2021_external_metric';ext.PROTOCOL=protocol('GOES17_GOES16_EXTERNAL_METRIC_REPLICATION_PROTOCOL.md')
    cas.ROOT=case;cas.OUT=out/'harmonization_error_cascade';cas.METRIC_OUT=tr.OUT;cas.EXP_OUT=ex.OUT;cas.FIRST_OUT=h.OUT
    bud.ROOT=case;bud.BASE=out;bud.OUT=out/'downstream_metric_framework';bud.FIRST=h.OUT;bud.EXPANDED=ex.OUT;bud.METRIC=tr.OUT;bud.CASCADE=cas.OUT
    syn.ROOT=case;syn.BASE=out;syn.OUT=bud.OUT;syn.EXTERNAL=ext.OUT;syn.CASCADE=cas.OUT
    for mod in M.values():
        if hasattr(mod,'OUT'):mod.OUT.mkdir(parents=True,exist_ok=True)
    return case,out,data,defs,expanded

def source_metadata(bucket,key):
    url=f'https://{bucket}.s3.amazonaws.com/{key}'
    name=hashlib.sha256(url.encode()).hexdigest()+'.json'
    p=PACKAGE_ROOT/'data/source_metadata'/name
    if not p.exists():
        raise FileNotFoundError('Offline source projection metadata is absent: '+url)
    row=json.loads(p.read_text())
    assert row['source_key']==key and row['source_url']==url
    return row
ra.source_metadata=source_metadata;va.source_metadata=source_metadata

def prepare(case,data,datasets=None):
    mechanism=importlib.import_module('analyze_goes_sunset_mechanism')
    rows=[]
    for d in (datasets or DATASETS):
        mechanism.DATA=data/d
        if not (mechanism.DATA/'goes_sunset_hourly.parquet').exists():raise FileNotFoundError(mechanism.DATA)
        out=case/'outputs'/d;out.mkdir(parents=True,exist_ok=True)
        f=pd.concat([mechanism.prepare_hourly(qa) for qa in ['strict','recommended']],ignore_index=True)
        f.to_parquet(out/'goes_sunset_hourly_analysis.parquet',index=False)
        rows.append({'dataset':d,'rows':len(f),'cities':int(f.uc_id.nunique()),'intervals':int(f.event_time_id.nunique()),'input_sha256':sha(mechanism.DATA/'goes_sunset_hourly.parquet')})
        print('PREPARED',rows[-1],flush=True)
    with (case/'prepared_analysis_inputs.jsonl').open('a') as f:
        for row in rows:f.write(json.dumps(row)+'\n')

def collect_input_manifest(mode,data):
    out=[]
    paths=[]
    for d in [*DATASETS,'goes18_2026_metric_holdout','goes19_2026_metric_holdout','goes16_2019_2021_external_metric','goes17_2019_2021_external_metric']:
        for name in ['goes_sunset_hourly.parquet','goes_sunset_city_events.csv','goes_sunset_cities.csv','FROZEN_SELECTION.json']:
            p=data/d/name
            if p.exists():paths.append(p)
    for p in paths:out.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['repaired'],default='repaired')
    ap.add_argument('--stages',default='all');ap.add_argument('--datasets',default='');a=ap.parse_args();case,out,data,defs,expanded=configure(a.mode)
    stages=['prepare','derive','validate','expansion_historical','expansion_validation','combine','selector','holdout','external','cascade','budget','synthesis'] if a.stages=='all' else a.stages.split(',')
    if a.mode=='baseline' and 'prepare' in stages:stages.remove('prepare')
    actions={'prepare':lambda:prepare(case,data,a.datasets.split(',') if a.datasets else None),'derive':h.derive,'validate':h.validate,
             'expansion_historical':lambda:ex.analyze('historical'),'expansion_validation':lambda:ex.analyze('validation'),
             'combine':ex.combine,'selector':tr.main,'holdout':va.main,'external':ext.main,
             'cascade':cas.main,'budget':bud.main,'synthesis':syn.main}
    inputs=collect_input_manifest(a.mode,data)
    (case/'input_manifest.json').write_text(json.dumps(inputs,indent=2))
    (case/'source_functions.json').write_text(json.dumps({n:{'path':m.__file__,'sha256':sha(m.__file__)} for n,m in M.items()},indent=2))
    for s in stages:
        t=time.monotonic();print('STAGE_START',s,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),flush=True)
        if s=='holdout':
            frozen={'model_sha256_before_holdout':sha(tr.MODEL_PATH),'manifest_sha256_before_holdout':sha(tr.OUT/'frozen_metric_aware_manifest.json'),
                    'note':'Repaired evaluation uses the unchanged prespecified algorithm and candidates; posthoc correction, not a newly untouched prospective test. Selection code uses2025only.',
                    'time_UTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
            (case/'selection_freeze_before_2026.json').write_text(json.dumps(frozen,indent=2))
        try:actions[s]();code=0
        except Exception:
            with (case/'run_journal.jsonl').open('a') as f:f.write(json.dumps({'stage':s,'exit_code':1,'elapsed_seconds':time.monotonic()-t,'traceback':traceback.format_exc()})+'\n')
            raise
        with (case/'run_journal.jsonl').open('a') as f:f.write(json.dumps({'stage':s,'exit_code':code,'elapsed_seconds':time.monotonic()-t,'command':sys.argv})+'\n')
        print('STAGE_DONE',s,'seconds',round(time.monotonic()-t,3),flush=True)
    assert all(sha(x['path'])==x['sha256'] for x in inputs),'Input mutation'
    if (case/'selection_freeze_before_2026.json').exists():
        frozen=json.loads((case/'selection_freeze_before_2026.json').read_text());assert sha(tr.MODEL_PATH)==frozen['model_sha256_before_holdout']
    print('PIPELINE_REQUESTED_STAGES_COMPLETE',a.mode,stages,flush=True)

if __name__=='__main__':main()
