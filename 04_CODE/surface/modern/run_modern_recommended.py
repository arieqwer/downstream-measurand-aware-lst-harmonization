from __future__ import annotations
from pathlib import Path
from datetime import date,datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor,as_completed
from threading import Lock,local
from io import StringIO
import argparse,json,hashlib,time,traceback,math,sys,re,os
import xml.etree.ElementTree as ET
import numpy as np,pandas as pd,requests,h5netcdf
from astral import Observer
from astral.sun import sun
from pyproj import CRS,Transformer,Geod
PACKAGE_ROOT=Path(__file__).resolve().parents[3]
ROOT=Path(os.environ.get('LST_MODERN_SURFACE_WORKSPACE',str(PACKAGE_ROOT/'outputs/modern_surface_native'))).resolve()
UTC=timezone.utc;LOCK=Lock();TLS=local();SIGMA=5.670374419e-8
STATIONS={'dra':dict(name='Desert Rock',lat=36.62373,lon=-116.01947,tz='America/Los_Angeles',eps=.966),'tbl':dict(name='Table Mountain',lat=40.12498,lon=-105.23680,tz='America/Denver',eps=.973),'fpk':dict(name='Fort Peck',lat=48.30783,lon=-105.10170,tz='America/Denver',eps=.979)}
CHRON=PACKAGE_ROOT/'02_EVIDENCE/si_tables/fixed_interval_chronology.csv'
_chron=pd.read_csv(CHRON);_modern=_chron[_chron.year.isin([2025,2026])]
WINDOWS=[(r.start_date,r.start_date,r.event_time_id) for r in _modern.itertuples()]
for d in ['raw/abi','raw/surfrad','results','logs']: (ROOT/d).mkdir(parents=True,exist_ok=True)

def safe(x):
 if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [safe(v) for v in x]
 if isinstance(x,np.ndarray):return safe(x.tolist())
 if isinstance(x,np.generic):return safe(x.item())
 if isinstance(x,bytes):return x.decode('utf8','replace')
 if isinstance(x,(datetime,date,pd.Timestamp)):return x.isoformat()
 if isinstance(x,Path):return str(x)
 if isinstance(x,float) and not np.isfinite(x):return None
 return x

def log(name,obj):
 with LOCK:
  with (ROOT/'logs'/name).open('a') as f:f.write(json.dumps(safe({'at_utc':datetime.now(UTC).isoformat(),**obj}))+'\n')

def sess():
 if not hasattr(TLS,'http'):TLS.http=requests.Session()
 return TLS.http

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def fetch(url,path,kind):
 if not path.exists() and kind=='surfrad':
  previous=Path(os.environ.get('LST_PROVIDER_CACHE',str(ROOT/'provider_cache')))/'surfrad'/path.relative_to(ROOT/'raw/surfrad')
  if previous.exists():
   path.parent.mkdir(parents=True,exist_ok=True);os.link(previous,path)
 if path.exists():
  log('downloads.jsonl',dict(url=url,path=path,kind=kind,status='existing',bytes=path.stat().st_size,sha256=sha(path)));return path
 path.parent.mkdir(parents=True,exist_ok=True)
 for attempt in range(1,4):
  tmp=path.with_suffix(path.suffix+f'.attempt{attempt}.part')
  start=time.time()
  try:
   with sess().get(url,timeout=(15,60),stream=True) as response:
    response.raise_for_status()
    with tmp.open('wb') as f:
     for chunk in response.iter_content(1024*1024):f.write(chunk)
   if kind=='abi':
    with tmp.open('rb') as f:assert f.read(8)==b'\x89HDF\r\n\x1a\n','Not HDF5'
   elif kind=='surfrad':assert 'version' in tmp.read_text().splitlines()[1], 'Not SURFRAD'
   tmp.rename(path);path.chmod(0o444)
   log('downloads.jsonl',dict(url=url,path=path,kind=kind,status='downloaded',attempt=attempt,bytes=path.stat().st_size,sha256=sha(path),seconds=time.time()-start));return path
  except Exception as e:
   log('failures.jsonl',dict(url=url,path=path,attempt=attempt,error=repr(e),seconds=time.time()-start))
   if attempt==3:raise
   time.sleep(attempt)
 raise RuntimeError(url)

def rd(var,key=slice(None)):
 raw=np.asarray(var[key]);a=var.attrs
 if str(safe(a.get('_Unsigned','false'))).lower()=='true' and np.issubdtype(raw.dtype,np.signedinteger):
  unsigned=np.dtype(f'u{raw.dtype.itemsize}');bits=raw.view(unsigned);fill=np.asarray(a.get('_FillValue',-1),dtype=raw.dtype).view(unsigned).item()
 else:bits=raw;fill=a.get('_FillValue',None)
 out=bits.astype('float64')*float(a.get('scale_factor',1))+float(a.get('add_offset',0))
 if fill is not None:out=np.where(bits==fill,np.nan,out)
 return out

def reqs(stage):
 rows=[]
 for start,end,eid in WINDOWS:
  for ts in pd.date_range(start,end):
   day=ts.date()
   if stage=='pilot' and day!=date(2026,6,1):continue
   for station,s in STATIONS.items():
    sunset=sun(Observer(latitude=s['lat'],longitude=s['lon']),date=day,tzinfo=ZoneInfo(s['tz']))['sunset'].astimezone(UTC)
    actual_local=sunset.astimezone(ZoneInfo(s['tz'])).date()
    corrected=sun(Observer(latitude=s['lat'],longitude=s['lon']),date=day,tzinfo=ZoneInfo(s['tz']))['sunset'].astimezone(UTC)
    for h in range(-3,7):
     target=(sunset+timedelta(hours=h,minutes=30)).replace(minute=0,second=0,microsecond=0)
     for bucket in ['noaa-goes18','noaa-goes19']:
      rows.append(dict(station=station,design_date=str(day),event_id=eid,sunset_utc=sunset.isoformat(),actual_sunset_local_date=str(actual_local),correct_local_day_sunset_utc=corrected.isoformat(),target_hour=h,target_utc=target.isoformat(),year=target.year,doy=target.timetuple().tm_yday,hour=target.hour,bucket=bucket))
 return pd.DataFrame(rows)

def inventory():
 rows=[]
 base=PACKAGE_ROOT/'data/corrected_inputs'
 for platform in ['goes18','goes19']:
  for year in [2025,2026]:
   folder=platform+('_2025_western_replication' if platform=='goes18' and year==2025 else '_2025_holdout' if year==2025 else '_2026_metric_holdout')
   path=base/folder/'goes_sunset_hourly.parquet'
   f=pd.read_parquet(path,columns=['source_key']).drop_duplicates()
   for k in f.source_key:
    bits=k.split('/');rows.append(dict(bucket='noaa-'+platform,year=int(bits[1]),doy=int(bits[2]),hour=int(bits[3]),key=k))
   log('inputs.jsonl',dict(path=path,sha256=sha(path),purpose='Retained native key/time inventory only'))
 out=pd.DataFrame(rows).drop_duplicates();assert not out.duplicated(['bucket','year','doy','hour']).any();return out

def lookup_missing(r):
 prefix=f'ABI-L2-LSTC/{int(r.year)}/{int(r.doy):03}/{int(r.hour):02}/'
 path=ROOT/'raw/inventory'/r.bucket/(prefix.replace('/','_')+'.xml');path.parent.mkdir(parents=True,exist_ok=True)
 url=f'https://{r.bucket}.s3.amazonaws.com/'
 if path.exists():content=path.read_bytes()
 else:
  response=sess().get(url,params={'list-type':'2','prefix':prefix,'max-keys':1000},timeout=60);response.raise_for_status();content=response.content;path.write_bytes(content);path.chmod(0o444)
 root=ET.fromstring(content);ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
 assert root.findtext('s:IsTruncated',namespaces=ns)=='false','truncated hour inventory'
 keys=[k.text for k in root.findall('.//s:Contents/s:Key',ns)]
 log('inventory.jsonl',dict(bucket=r.bucket,prefix=prefix,url=url,keys=keys,path=path,sha256=sha(path)))
 assert len(keys)<=1,(prefix,len(keys))
 return dict(bucket=r.bucket,year=r.year,doy=r.doy,hour=r.hour,key=keys[0] if keys else None)

def decode_scan(bucket,key):
 name=Path(key).name;path=ROOT/'raw/abi'/bucket/name
 peer=Path(os.environ.get('LST_PROVIDER_CACHE',str(ROOT/'provider_cache')))/'abi'/bucket/name
 if peer.exists() and not path.exists():
  # Reuse peer bytes via hard link; do not modify the peer file or its permissions.
  path.parent.mkdir(parents=True,exist_ok=True);os.link(peer,path)
 url=f'https://{bucket}.s3.amazonaws.com/{key}'
 fetch(url,path,'abi')
 with h5netcdf.File(path,'r',phony_dims='sort') as d:
  p=safe(dict(d.variables['goes_imager_projection'].attrs));height=float(p['perspective_point_height'])
  crs=CRS.from_proj4(f"+proj=geos +h={height} +lon_0={p['longitude_of_projection_origin']} +sweep={p.get('sweep_angle_axis','x')} +a={p['semi_major_axis']} +b={p['semi_minor_axis']} +units=m +no_defs")
  fw=Transformer.from_crs('EPSG:4326',crs,always_xy=True);inv=Transformer.from_crs(crs,'EPSG:4326',always_xy=True)
  xs=rd(d.variables['x']);ys=rd(d.variables['y']);v=d.variables['LST'];dq=d.variables['DQF']
  attrs=safe(dict(d.attrs));small={}
  for n in ['FPT_mitigation_flag','FPM_temperature','algorithm_product_version_container','processing_parm_version_container','algorithm_dynamic_input_data_container']:
   if n in d.variables:
    vv=d.variables[n];small[n]={'attrs':safe(dict(vv.attrs)),'value':safe(np.asarray(vv[...])) if np.prod(vv.shape or (1,))<100 else 'not read'}
  start=pd.Timestamp(attrs['time_coverage_start']);end=pd.Timestamp(attrs['time_coverage_end']);mid=start+(end-start)/2
  metadata=dict(url=url,path=str(path),sha256=sha(path),bucket=bucket,key=key,global_attrs=attrs,lst_attrs=safe(dict(v.attrs)),dqf_attrs=safe(dict(dq.attrs)),projection=safe(p),additional=small)
  meta=ROOT/'raw/abi'/bucket/(name+'.metadata.json')
  if not meta.exists():meta.write_text(json.dumps(safe(metadata),indent=2));meta.chmod(0o444)
  out=[]
  for code,s in STATIONS.items():
   px,py=fw.transform(s['lon'],s['lat']);sx=px/height;sy=py/height
   col=int(np.argmin(abs(xs-sx)));row=int(np.argmin(abs(ys-sy)));inside=np.isfinite(px) and xs.min()<=sx<=xs.max() and ys.min()<=sy<=ys.max()
   values=rd(v,(slice(max(0,row-1),row+2),slice(max(0,col-1),col+2)))
   flags=np.asarray(dq[max(0,row-1):row+2,max(0,col-1):col+2])
   point=float(rd(v,(row,col)));flag=int(dq[row,col]);physical=(values>=180)&(values<=380)&np.isfinite(values)
   strict=physical&(flags==0);recommended=physical&(flags<=1);validpoint=inside and np.isfinite(point) and 180<=point<=380 and flag in [0,1]
   lo,la=inv.transform(xs[col]*height,ys[row]*height);_,_,dist=Geod(ellps='WGS84').inv(s['lon'],s['lat'],lo,la)
   rx,ry=fw.transform(lo,la);roundtrip=float(np.hypot(rx-xs[col]*height,ry-ys[row]*height))
   belowlon,belowlat=inv.transform(xs[min(col+1,len(xs)-1)]*height,ys[row]*height);_,_,dx=Geod(ellps='WGS84').inv(lo,la,belowlon,belowlat)
   abovelon,abovelat=inv.transform(xs[col]*height,ys[min(row+1,len(ys)-1)]*height);_,_,dy=Geod(ellps='WGS84').inv(lo,la,abovelon,abovelat)
   out.append(dict(bucket=bucket,key=key,station=code,scan_start=start.isoformat(),scan_end=end.isoformat(),scan_mid=mid.isoformat(),row=row,col=col,grid_inside=bool(inside),center_lon=lo,center_lat=la,center_distance_m=dist,pixel_spacing_x_m=dx,pixel_spacing_y_m=dy,projection_roundtrip_m=roundtrip,point_dqf=flag,point_raw_lst_k=point,point_valid_q0=bool(inside and np.isfinite(point) and 180<=point<=380 and flag==0),point_valid_q01=bool(validpoint),point_lst_k=point if validpoint else np.nan,neighborhood_n_q0=int(strict.sum()),neighborhood_n_q01=int(recommended.sum()),neighborhood_mean_q0_k=float(values[strict].mean()) if strict.sum()>=5 else np.nan,neighborhood_std_q0_k=float(values[strict].std()) if strict.sum()>=2 else np.nan,neighborhood_range_q0_k=float(np.ptp(values[strict])) if strict.sum()>=2 else np.nan,fpt_mitigation_flag=json.dumps(small.get('FPT_mitigation_flag',{})),native_path=str(path)))
  return out

def ground(code,day):
 d=pd.Timestamp(day).date();doy=d.timetuple().tm_yday;name=f'{code}{str(d.year)[2:]}{doy:03}.dat';url=f'https://gml.noaa.gov/aftp/data/radiation/surfrad/{code}/{d.year}/{name}';path=ROOT/'raw/surfrad'/code/str(d.year)/name
 fetch(url,path,'surfrad');text=path.read_text();lines=text.splitlines();coords=lines[1].split();s=STATIONS[code]
 assert abs(float(coords[0])-s['lat'])<.01 and abs(float(coords[1])-s['lon'])<.01,(code,coords)
 a=np.loadtxt(StringIO('\n'.join(lines[2:])));assert a.shape[1]==48,a.shape
 times=pd.to_datetime(dict(year=a[:,0].astype(int),month=a[:,2].astype(int),day=a[:,3].astype(int),hour=a[:,4].astype(int),minute=a[:,5].astype(int)),utc=True)
 f=pd.DataFrame(dict(time=times,lw_down=a[:,16],qc_down=a[:,17].astype(int),lw_up=a[:,22],qc_up=a[:,23].astype(int),air_temp_c=a[:,38],file=str(path),file_sha256=sha(path),header_lat=float(coords[0]),header_lon=float(coords[1])))
 assert f.time.is_unique and f.time.is_monotonic_increasing
 f['sample_center']=f.time-pd.Timedelta(seconds=30)
 f['valid']=(f.qc_down==0)&(f.qc_up==0)&(f.lw_down>0)&(f.lw_up>0)
 return f

def temp(up,down,eps):return ((up-(1-eps)*down)/(eps*SIGMA))**.25

def analyze(f,stage):
 gs={};tasks=set()
 for r in f.itertuples():
  t=pd.Timestamp(r.scan_mid)
  for d in [(t-pd.Timedelta(minutes=8)).date(),(t+pd.Timedelta(minutes=8)).date()]:tasks.add((r.station,d))
 with ThreadPoolExecutor(max_workers=3) as ex:
  fut={ex.submit(ground,*t):t for t in sorted(tasks)}
  for future in as_completed(fut):
   code,d=fut[future]
   try:
    value=future.result();gs.setdefault(code,[]).append(value)
   except Exception as e:log('failures.jsonl',dict(stage=stage,kind='ground',station=code,day=str(d),error=repr(e)))
 gf={c:pd.concat(v,ignore_index=True).drop_duplicates('time').sort_values('time') for c,v in gs.items()}
 out=[]
 for r in f.to_dict('records'):
  code=r['station'];t=pd.Timestamp(r['scan_mid']);s=STATIONS[code];g=gf.get(code,pd.DataFrame())
  selection=g[(g.sample_center>t-pd.Timedelta(minutes=7.5))&(g.sample_center<=t+pd.Timedelta(minutes=7.5))] if not g.empty else g
  valid=selection[selection.valid] if not selection.empty else selection
  r.update(ground_total_minutes=len(selection),ground_qc0_minutes=len(valid),ground_valid=len(valid)>=12,literature_eps=s['eps'],ground_reference_kind='SURFRAD longwave-derived radiometric temperature with assumed historical emissivity',actual_scan_local_date=str(t.tz_convert(s['tz']).date()))
  if len(valid)>=12:
   up=float(valid.lw_up.mean());down=float(valid.lw_down.mean());r.update(lw_up_mean=up,lw_down_mean=down,ground_lst_k=float(temp(up,down,s['eps'])),ground_lst_eps_minus01_k=float(temp(up,down,s['eps']-.01)),ground_lst_eps_plus01_k=float(temp(up,down,s['eps']+.01)),ground_lst_eps097_k=float(temp(up,down,.97)),ground_first_minute=valid.time.min().isoformat(),ground_last_minute=valid.time.max().isoformat(),ground_mean_sample_center_offset_seconds=float((valid.sample_center-t).dt.total_seconds().mean()),ground_timestamp_semantics='stored times are averaging ends; selection uses end minus30seconds')
   nearest=valid.iloc[int(np.argmin(abs((valid.sample_center-t).dt.total_seconds())))]
   r.update(ground_nearest_offset_seconds=float((nearest.sample_center-t).total_seconds()),ground_nearest_lst_k=float(temp(nearest.lw_up,nearest.lw_down,s['eps'])))
  out.append(r)
 allrows=pd.DataFrame(out);allrows.to_csv(ROOT/'results'/f'{stage}_matchups_all.csv',index=False)
 allrows.to_parquet(ROOT/'results'/f'{stage}_matchups_all.parquet',index=False)
 valid=allrows[allrows.point_valid_q01 & allrows.ground_valid].copy()
 keys=['station','design_date','target_hour'];counts=valid.groupby(keys).bucket.nunique();commonkeys=counts[counts==2].reset_index()[keys]
 paired=valid.merge(commonkeys,on=keys,validate='many_to_one')
 if not paired.empty:
  stamps=paired.groupby(keys).scan_start.apply(lambda a:(pd.to_datetime(a,utc=True,format='ISO8601').max()-pd.to_datetime(a,utc=True,format='ISO8601').min()).total_seconds()).reset_index(name='platform_scan_separation_seconds')
  paired=paired.merge(stamps,on=keys,validate='many_to_one');paired=paired[paired.platform_scan_separation_seconds<=60].copy()
  paired['residual_k']=paired.point_lst_k-paired.ground_lst_k
  paired['residual_neighbor_k']=paired.neighborhood_mean_q0_k-paired.ground_lst_k
  paired['july_event_overlap']=pd.to_datetime(paired.scan_mid,utc=True,format='ISO8601').dt.strftime('%Y-%m-%d').isin(['2021-07-09','2021-07-22','2021-07-23'])
 paired.to_csv(ROOT/'results'/f'{stage}_matchups_common.csv',index=False)
 paired.to_parquet(ROOT/'results'/f'{stage}_matchups_common.parquet',index=False)
 metrics=[]
 for dimension in ['pooled','year','station','target_hour','event_id']:
  groups=[('all',paired)] if dimension=='pooled' else list(paired.groupby(dimension))
  for group,z in groups:
   for bucket,y in z.groupby('bucket'):
    e=y.residual_k.to_numpy();metrics.append(dict(dimension=dimension,group=group,bucket=bucket,n=len(y),stations=y.station.nunique(),days=y.design_date.nunique(),bias=float(e.mean()),rmse=float(np.mean(e*e)**.5),mae=float(abs(e).mean()),median_error=float(np.median(e)),ground_mean=float(y.ground_lst_k.mean()),satellite_mean=float(y.point_lst_k.mean())))
 pd.DataFrame(metrics).to_csv(ROOT/'results'/f'{stage}_metrics.csv',index=False)
 summary=dict(stage=stage,requested_station_satellite_rows=len(pd.read_csv(ROOT/'results'/f'{stage}_requests_all.csv')),native_present_rows=len(allrows),requested_rows=len(allrows),all_stations=allrows.station.nunique(),native_files=allrows.key.nunique(),point_qc0_rows=int(allrows.point_valid_q0.sum()),point_qc01_rows=int(allrows.point_valid_q01.sum()),ground_qc0_rows=int(allrows.ground_valid.sum()),common_rows=len(paired),common_matchups=len(paired)//2,common_stations=paired.station.nunique(),common_design_days=paired.design_date.nunique(),max_projection_roundtrip_m=float(allrows.projection_roundtrip_m.max()),max_scan_pair_separation_seconds=float(paired.platform_scan_separation_seconds.max()) if not paired.empty else None,metrics=metrics)
 (ROOT/'results'/f'{stage}_summary.json').write_text(json.dumps(safe(summary),indent=2));print(json.dumps(safe(summary),indent=2),flush=True)
 return paired

def independent_checks(f):
 truth=np.array([270.,300.,330.]);eps=np.array([.95,.97,.99]);down=np.array([220.,300.,420.]);up=eps*SIGMA*truth**4+(1-eps)*down
 assert np.max(abs(temp(up,down,eps)-truth))<1e-10
 assert abs(temp(SIGMA*300**4,270,1)-300)<1e-10
 assert f.projection_roundtrip_m.max()<1
 checks={'greybody_recovery_max_k':float(np.max(abs(temp(up,down,eps)-truth))),'blackbody_control_k':float(temp(SIGMA*300**4,270,1)),'projection_roundtrip_max_m':float(f.projection_roundtrip_m.max())}
 # Independent native CF decode replay through netCDF4 automatic scaling on one file per platform.
 import netCDF4
 errors=[]
 for bucket,z in f.groupby('bucket'):
  r=z[z.point_raw_lst_k.notna()].iloc[0]
  with netCDF4.Dataset(r.native_path) as d:
   vv=d.variables['LST'][int(r.row),int(r.col)]
   if not np.ma.is_masked(vv) and np.isfinite(r.point_raw_lst_k):errors.append(float(vv-r.point_raw_lst_k))
 assert not errors or max(abs(e) for e in errors)<1e-4,errors
 checks['netcdf4_independent_cf_decode_errors_k']=errors
 (ROOT/'results'/'acceptance_checks.json').write_text(json.dumps(checks,indent=2))

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['pilot','full'],default='pilot');parser.add_argument('--analyze-only',action='store_true');args=parser.parse_args()
 started=time.time();rf=reqs(args.stage);inv=inventory();rf=rf.merge(inv,on=['bucket','year','doy','hour'],how='left',validate='many_to_one')
 if rf.key.isna().any():
  missing=rf[rf.key.isna()][['bucket','year','doy','hour']].drop_duplicates();more=[]
  with ThreadPoolExecutor(max_workers=1) as ex:
   for value in ex.map(lookup_missing,missing.itertuples(index=False)):more.append(value)
  extra=pd.DataFrame(more);rf=rf.drop(columns=['key','old_scan_start']).merge(pd.concat([inv,extra],ignore_index=True),on=['bucket','year','doy','hour'],how='left',validate='many_to_one')
 rf.to_csv(ROOT/'results'/f'{args.stage}_requests_all.csv',index=False)
 rf[rf.key.isna()].to_csv(ROOT/'results'/f'{args.stage}_missing_inventory.csv',index=False)
 rf=rf[rf.key.notna()].copy()
 rf.to_csv(ROOT/'results'/f'{args.stage}_requests.csv',index=False)
 timeaudit=[]
 for code,s in STATIONS.items():
  o=Observer(latitude=s['lat'],longitude=s['lon']);day=date(2026,6,1);u=sun(o,date=day,tzinfo=ZoneInfo(s['tz']))['sunset'].astimezone(UTC);l=sun(o,date=day,tzinfo=ZoneInfo(s['tz']))['sunset'].astimezone(UTC)
  timeaudit.append(dict(station=code,design_date=str(day),existing_convention_sunset_utc=u.isoformat(),existing_convention_actual_local_date=str(u.astimezone(ZoneInfo(s['tz'])).date()),correct_local_day_sunset_utc=l.isoformat(),difference_hours=(l-u).total_seconds()/3600))
 (ROOT/'results'/'timing_audit.json').write_text(json.dumps({'source_script':str(Path(__file__)),'code_behavior':'Repaired: sunset requested with station civil timezone for declared local date, converted toUTC, thennearesthour.','stations':timeaudit},indent=2))
 tasks=rf[['bucket','key']].drop_duplicates();assert len(tasks)<=1000
 print('Stage',args.stage,'native files',len(tasks),'requested station/satellite rows',len(rf),flush=True)
 out=[]
 if args.analyze_only:
  f=pd.read_parquet(ROOT/'results'/f'{args.stage}_native_extracted.parquet')
 else:
  with ThreadPoolExecutor(max_workers=5) as ex:
   futures={ex.submit(decode_scan,r.bucket,r.key):(r.bucket,r.key) for r in tasks.itertuples(index=False)}
   for i,future in enumerate(as_completed(futures),1):
    try:out.extend(future.result())
    except Exception as e:
     log('failures.jsonl',dict(stage=args.stage,kind='abi',bucket=futures[future][0],key=futures[future][1],error=traceback.format_exc()))
    if i%20==0 or i==len(tasks):print('Native',i,'/',len(tasks),'elapsed',round(time.time()-started,1),'seconds',flush=True)
  f=pd.DataFrame(out);f=f.merge(rf,on=['bucket','key','station'],validate='one_to_many');f.to_parquet(ROOT/'results'/f'{args.stage}_native_extracted.parquet',index=False)
 independent_checks(f);analyze(f,args.stage)
 log('runs.jsonl',dict(stage=args.stage,command=sys.argv,seconds=time.time()-started,python=sys.version,numpy=np.__version__,pandas=pd.__version__,h5netcdf=h5netcdf.__version__))
if __name__=='__main__':main()
