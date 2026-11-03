from pathlib import Path
import os
PACKAGE_ROOT=Path(__file__).resolve().parents[2]
NATIVE_WORKSPACE=Path(os.environ.get("LST_NATIVE_WORKSPACE",str(PACKAGE_ROOT/"data/native_workspace"))).resolve()
import json,hashlib,time,sys,re
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np,pandas as pd,requests,h5netcdf,xarray as xr
B=NATIVE_WORKSPACE/'auxiliary/native';S=PACKAGE_ROOT/'data/corrected_inputs';H=NATIVE_WORKSPACE/'previous_source_workspace'
PLAN=B/'results/audit_selection_predeclared.json'
def conv(v):
 if isinstance(v,np.ndarray):return [conv(x) for x in v.tolist()] if v.ndim else conv(v.item())
 if isinstance(v,np.generic):return conv(v.item())
 if isinstance(v,bytes):return v.decode('utf-8',errors='replace')
 if isinstance(v,(list,tuple)):return [conv(x) for x in v]
 if isinstance(v,dict):return {str(k):conv(val) for k,val in v.items()}
 return v

def getpath(bucket,key):
 name=Path(key).name;p=B/'raw'/bucket/name
 p.parent.mkdir(parents=True,exist_ok=True)
 candidates=[NATIVE_WORKSPACE/'extraction/raw'/bucket/name, NATIVE_WORKSPACE/'previous_source_workspace'/bucket/name, NATIVE_WORKSPACE/'previous_source_workspace'/bucket/name, NATIVE_WORKSPACE/'previous_source_workspace'/name, B.parent/'surface/raw/abi'/bucket/name]
 for other in candidates:
  if not p.exists() and other.exists():return other
 if p.exists():return p
 url=f'https://{bucket}.s3.amazonaws.com/{key}'
 t=time.monotonic();r=requests.get(url,timeout=(15,90));r.raise_for_status();assert r.content.startswith(b'\x89HDF\r\n\x1a\n')
 tmp=p.with_suffix('.tmp');tmp.write_bytes(r.content);tmp.replace(p);p.chmod(0o444)
 with (B/'logs/downloads.jsonl').open('a') as f:f.write(json.dumps(dict(url=url,path=str(p),bytes=p.stat().st_size,seconds=time.monotonic()-t,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))+'\n')
 return p

def audit(item):
 p=getpath(item['bucket'],item['key']);t=time.monotonic()
 with h5netcdf.File(p,'r',phony_dims='sort') as d:
  metadata={k:conv(v) for k,v in d.attrs.items()}
  variables={}
  names=['LST','DQF','PQI','x','y','goes_imager_projection','FPT_mitigation_flag','algorithm_dynamic_input_data_container','processing_parm_version_container','algorithm_product_version_container','percent_good_retrieval_data','percent_valid_retrieval_data']
  for n in names:
   if n not in d.variables:continue
   v=d.variables[n];entry={'shape':list(v.shape),'dtype':str(v.dtype),'attrs':conv(dict(v.attrs))}
   if np.prod(v.shape)<=10:
    try:entry['value']=conv(v[()])
    except:pass
   variables[n]=entry
  q=np.asarray(d.variables['DQF'][:]);vals,counts=np.unique(q,return_counts=True)
  attrs=d.variables['LST'].attrs;packed=np.asarray(d.variables['LST'][:]);raw=packed.view(np.dtype(f'u{packed.dtype.itemsize}')) if str(attrs.get('_Unsigned','false')).lower()=='true' and packed.dtype.kind=='i' else packed
  fill=np.asarray(attrs['_FillValue'],dtype=packed.dtype).view(raw.dtype).item() if raw.dtype!=packed.dtype else attrs['_FillValue']
  decoded=raw.astype(np.float64)*float(attrs['scale_factor'])+float(attrs['add_offset']);valid=(raw!=fill)&np.isfinite(decoded)
  summary={'dqf_counts':dict(zip([str(x) for x in vals.tolist()],[int(x) for x in counts])),'pixels':int(raw.size),'nonfill_LST_pixels':int(valid.sum()),'dqf0_nonfill':int(((q==0)&valid).sum()),'dqf01_nonfill':int(((q<=1)&valid).sum()),'LST_nonfill_min':float(decoded[valid].min()) if valid.any() else None,'LST_nonfill_max':float(decoded[valid].max()) if valid.any() else None}
 with xr.open_dataset(p,engine="h5netcdf") as ds:
  xv=np.asarray(ds.LST.values);mask=valid&np.isfinite(xv);err=float(np.abs(decoded[mask]-xv[mask]).max()) if mask.any() else None
  assert err is None or err<1e-3,(p,err)
 summary['independent_CF_decode_max_abs_K']=err
 out={**item,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'global':metadata,'variables':variables,'summary':summary}
 (B/'results'/f"{item['label']}_metadata.json").write_text(json.dumps(out,indent=2,allow_nan=True))
 print(item['label'],item['bucket'],variables['DQF']['attrs'].get('flag_meanings'),summary,flush=True)
 return out

def select():
 records=[]
 specs=[('historical',H/'GOES16_sunset_hourly.parquet','noaa-goes16',[2019,2020,2021]),('historical',H/'GOES17_sunset_hourly.parquet','noaa-goes17',[2019,2020,2021]),('modern',S/'goes_sunset_confirmation/goes_sunset_hourly.parquet','noaa-goes16',[2022,2024]),('modern',S/'goes18_2022_2024_same_sensor/goes_sunset_hourly.parquet','noaa-goes18',[2022,2024]),('modern',S/'goes18_2025_western_replication/goes_sunset_hourly.parquet','noaa-goes18',[2025]),('modern',S/'goes19_2025_holdout/goes_sunset_hourly.parquet','noaa-goes19',[2025])]
 for kind,path,bucket,years in specs:
  df=pd.read_parquet(path)
  for year in years:
   candidates=df.loc[df.event_year.eq(year),'source_key'].drop_duplicates().sort_values()
   records.append(dict(label=f'{bucket}_{year}_first',bucket=bucket,key=candidates.iloc[0],selection='first chronological native source key in retained study extract',source_summary=str(path)))
 # Event-overlap checks use exactly retained native scans closest to09UTC onJuly9and23.
 df=pd.read_parquet(H/'GOES17_sunset_hourly.parquet');keys=df.source_key.drop_duplicates()
 for day,doy in [('2021-07-09','190'),('2021-07-23','204')]:
  k=keys[keys.str.contains(f'/2021/{doy}/')].tolist();k.sort(key=lambda x:abs(int(x.split('/')[3])-9));records.append(dict(label=f'noaa-goes17_{day}_09UTC',bucket='noaa-goes17',key=k[0],selection='retained study file closest to09UTC within documented event date',source_summary=str(H/'GOES17_sunset_hourly.parquet')))
 # Predeclared spatial illustration cityPhoenix4699, firstholdoutdesignlocal_dateJune1, hours−3/+4. No outcome/cloud inspection selects scenes.
 for bucket,d in [('noaa-goes18','goes18_2026_metric_holdout'),('noaa-goes19','goes19_2026_metric_holdout')]:
  path=S/d/'goes_sunset_hourly.parquet';df=pd.read_parquet(path);df.uc_id=df.uc_id.astype(str)
  for h in [-3,4]:
   r=df[df.uc_id.eq('4699')&df.local_date.eq('2026-06-01')&df.target_hour_from_sunset.eq(h)].iloc[0]
   records.append(dict(label=f'{bucket}_2026_phoenix_h{h:+d}',bucket=bucket,key=r.source_key,selection='Phoenix4699firstholdoutdateJune1hoursminus3plus4fixedbeforeviewingrasters',source_summary=str(path),uc_id='4699',local_date=r.local_date,target_hour=h,sunset_utc=r.sunset_utc,scan_time_utc=r.scan_time_utc))
 return records
if __name__=='__main__':
 if not PLAN.exists():PLAN.write_text(json.dumps({'criteria':'Study-source provenance; exact quality/packingmetadata; manualCFagreement<1e-3K; no oldoutputs overwritten; mapselectionindependentoferrors; cloud/LHPchecksdescriptiveonly','records':select(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
 records=json.loads(PLAN.read_text())['records'];outs=[];errors=[]
 # modern2026first soqualityagent receives definitions promptly; no more than2fullgrids concurrent.
 records.sort(key=lambda x:(0 if '_2026_' in x['label'] else 1,x['label']))
 with ThreadPoolExecutor(max_workers=1) as pool:
  futures={pool.submit(audit,x):x for x in records}
  for f in as_completed(futures):
   try:outs.append(f.result())
   except Exception as e:errors.append({'item':futures[f],'error':repr(e)});print('ERROR',errors[-1],flush=True)
 (B/'results/native_audit_summary.json').write_text(json.dumps({'files':outs,'errors':errors},indent=2,allow_nan=True))
 print('DONE',len(outs),'errors',len(errors),flush=True)
