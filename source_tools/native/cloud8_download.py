from pathlib import Path
import os
PACKAGE_ROOT=Path(__file__).resolve().parents[2]
NATIVE_WORKSPACE=Path(os.environ.get("LST_NATIVE_WORKSPACE",str(PACKAGE_ROOT/"data/native_workspace"))).resolve()
import pandas as pd,json,hashlib
from native_audit import audit
B=NATIVE_WORKSPACE/'auxiliary/native';S=PACKAGE_ROOT/'data/corrected_inputs'
P=B/'results/cloud8_selection_predeclared.json'
if not P.exists():
 intervals=pd.read_csv(S/'goes18_2026_metric_holdout/goes_sunset_intervals.csv');records=[]
 for bucket,di in [('noaa-goes18','goes18_2026_metric_holdout'),('noaa-goes19','goes19_2026_metric_holdout')]:
  df=pd.read_parquet(S/di/'goes_sunset_hourly.parquet');df.uc_id=df.uc_id.astype(str)
  for date in intervals.start_date:
   for h in [-3,4]:
    r=df[df.uc_id.eq('4699')&df.local_date.eq(date)&df.target_hour_from_sunset.eq(h)].iloc[0]
    records.append(dict(label=f'{bucket}_2026_phoenix_{date}_h{h:+d}',bucket=bucket,key=r.source_key,selection='systematicfirstdesign-dayofeachofeightintervals;Phoenixcity4699hminus3plus4;nofilechosenbyerrororcloud',source_summary=str(S/di/'goes_sunset_hourly.parquet'),uc_id='4699',local_date=date,target_hour=h,sunset_utc=r.sunset_utc,scan_time_utc=r.scan_time_utc,event_time_id=int(r.event_time_id)))
 assert len(records)==32
 P.write_text(json.dumps({'selection_rule':'firstdesign-dayofeachpre-existing8holdoutintervals;2Phoenixrelativehours;75cityspatialsupport;initialone-daypilotverifiedtechnicalfeasibility;expandedbyfixedcoverage-rulenoterror;posthocrevisiondiagnostic','masks':['DQF0-1','DQF0','ACMclear','ACMclear1pixelcloudbuffer','ACMclear2pixelcloudbuffer'],'records':records,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
records=json.loads(P.read_text())['records'];outs=[];errors=[]
for item in records:
 try:outs.append(audit(item))
 except Exception as e:errors.append({'record':item,'error':repr(e)});print('ERROR',errors[-1],flush=True)
(B/'results/cloud8_audit_summary.json').write_text(json.dumps({'files':outs,'errors':errors},indent=2));assert len(outs)==32 and not errors
print('DONE32',flush=True)
