"""Repair local-calendar allocation and complete-polygon support; immutable sources."""
from __future__ import annotations
from pathlib import Path
import os
PACKAGE_ROOT=Path(__file__).resolve().parents[2]
NATIVE_WORKSPACE=Path(os.environ.get("LST_NATIVE_WORKSPACE",str(PACKAGE_ROOT/"data/native_workspace"))).resolve()
from datetime import timedelta,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import os,sys,json,hashlib,time,threading,shutil,traceback,argparse
import numpy as np,pandas as pd,requests,h5netcdf
from astral import Observer
from astral.sun import sun
from shapely.geometry import shape
from shapely import contains_xy
from pyproj import CRS,Transformer

B=NATIVE_WORKSPACE/'extraction'
SCI=PACKAGE_ROOT/'data/corrected_inputs'
PREV=NATIVE_WORKSPACE/'previous_source_workspace'
for d in ['raw','logs','masks','grid_catalog','corrected_data','parts']: (B/d).mkdir(exist_ok=True,parents=True)
UTC=timezone.utc;LOCK=threading.Lock();TLS=threading.local()
CONFIGS=[
 ('goes16_2018_2024_full_census',16,'goes18_2022_2024_same_sensor'),
 ('goes18_2022_2024_same_sensor',18,None),
 ('goes16_2018_2024_low_green',16,'goes18_2022_2024_expansion'),
 ('goes18_2022_2024_expansion',18,None),
 ('goes18_2025_western_replication',18,None),
 ('goes19_2025_holdout',19,'goes18_2025_western_replication'),
 ('goes18_2025_expansion',18,None),
 ('goes19_2025_low_green',19,'goes18_2025_expansion'),
 ('goes16_2019_2021_external_metric',16,None),
 ('goes17_2019_2021_external_metric',17,None),
 ('goes18_2026_metric_holdout',18,None),
 ('goes19_2026_metric_holdout',19,None)]
BASECOLS=['uc_id','event_year','event_step8','event_time_id','local_date','sunset_utc','target_hour_from_sunset','scan_time_utc','actual_hour_from_sunset','source_key']
REGCOLS=[f'{u}_{q}_{v}' for u in ['core','ring'] for q in ['strict','recommended'] for v in ['count','lst_k']]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(x):
 if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [safe(v) for v in x]
 if isinstance(x,np.ndarray):return safe(x.tolist())
 if isinstance(x,np.generic):return safe(x.item())
 if isinstance(x,bytes):return x.decode()
 if isinstance(x,Path):return str(x)
 return x
def log(name,row):
 with LOCK:
  with (B/'logs'/name).open('a') as f:f.write(json.dumps(safe(row))+'\n')
def session():
 if not hasattr(TLS,'s'):TLS.s=requests.Session()
 return TLS.s
def raw(bucket,key):
 p=B/'raw'/bucket/Path(key).name;p.parent.mkdir(exist_ok=True)
 if not p.exists():
  candidates=[PREV/'native/raw'/bucket/p.name,PREV/'surface/raw/abi'/bucket/p.name,PREV/'calendar/raw'/p.name,
              B.parent/'auxiliary/surface/raw/abi'/bucket/p.name]
  peer=next((x for x in candidates if x.exists()),None)
  if peer:
   try:os.link(peer,p)
   except FileExistsError:pass
   log('raw_downloads.jsonl',dict(bucket=bucket,key=key,path=p,reused_from=peer,sha256=sha(p),bytes=p.stat().st_size))
  else:
   for attempt in range(1,5):
    try:
     r=session().get(f'https://{bucket}.s3.amazonaws.com/{key}',timeout=(15,90));r.raise_for_status();assert r.content.startswith(b'\x89HDF\r\n\x1a\n')
     tmp=p.with_suffix('.download.part');tmp.write_bytes(r.content);tmp.chmod(0o444);tmp.rename(p)
     log('raw_downloads.jsonl',dict(bucket=bucket,key=key,path=p,url=r.url,sha256=sha(p),bytes=len(r.content),attempt=attempt));break
    except Exception as e:
     log('download_failures.jsonl',dict(bucket=bucket,key=key,attempt=attempt,error=repr(e)))
     if attempt==4:raise
     time.sleep(min(attempt*2,6))
 return p
def grid(p):
 with h5netcdf.File(p,'r',phony_dims='sort') as d:
  axes=[]
  for n in ['x','y']:
   v=d.variables[n];axes.append(np.asarray(v[:],dtype='float64')*float(v.attrs.get('scale_factor',1))+float(v.attrs.get('add_offset',0)))
  proj=safe(dict(d.variables['goes_imager_projection'].attrs))
  meta=dict(path=str(p),sha256=sha(p),x_attrs=safe(dict(d.variables['x'].attrs)),y_attrs=safe(dict(d.variables['y'].attrs)),projection=proj,
            platform=safe(d.attrs.get('platform_ID')),time_start=safe(d.attrs['time_coverage_start']))
 return axes[0],axes[1],meta
def signature(xs,ys,meta):
 return hashlib.sha256(xs.tobytes()+ys.tobytes()+json.dumps(meta['projection'],sort_keys=True).encode()).hexdigest()
def polygon_vertices(g):
 out=[]
 for z in (list(g.geoms) if hasattr(g,'geoms') else [g]):
  for ring in [z.exterior,*z.interiors]:
   a=np.asarray(ring.coords);out.append(a)
   # Densify long edges before projecting, to bound projection curvature.
   dense=[]
   for l,r in zip(a[:-1],a[1:]):
    n=max(1,int(np.ceil(np.max(abs(r-l))/.005)))
    dense.extend(l+(r-l)*t for t in np.arange(n)/n)
   out.append(np.asarray(dense))
 return np.concatenate(out)
def masks_for(name,cities,geoms,p):
 xs,ys,meta=grid(p);proj=meta['projection'];h=float(proj['perspective_point_height'])
 crs=CRS.from_proj4(f"+proj=geos +h={h} +lon_0={proj['longitude_of_projection_origin']} +sweep={proj.get('sweep_angle_axis','x')} +a={proj['semi_major_axis']} +b={proj['semi_minor_axis']} +units=m")
 fw=Transformer.from_crs('EPSG:4326',crs,always_xy=True);inv=Transformer.from_crs(crs,'EPSG:4326',always_xy=True)
 masks={};arrays={};audit=[]
 for city in cities.itertuples(index=False):
  cx,cy=fw.transform(city.lon,city.lat)
  # Reproduce old round(offset/scale) centre selection in float64.
  c=int(round((cx/h-float(meta['x_attrs']['add_offset']))/float(meta['x_attrs']['scale_factor'])))
  r=int(round((cy/h-float(meta['y_attrs']['add_offset']))/float(meta['y_attrs']['scale_factor'])))
  for unit in ['core','ring']:
   geom=geoms[(city.uc_id,unit)];verts=polygon_vertices(geom);px,py=fw.transform(verts[:,0],verts[:,1]);sx=np.asarray(px)/h;sy=np.asarray(py)/h
   assert np.isfinite(sx).all() and np.isfinite(sy).all(),(name,city.uc_id,unit)
   dx=max(abs(np.diff(xs)));dy=max(abs(np.diff(ys)))
   def select(pad):
    cc=np.flatnonzero((xs>=sx.min()-pad*dx)&(xs<=sx.max()+pad*dx));rr=np.flatnonzero((ys>=sy.min()-pad*dy)&(ys<=sy.max()+pad*dy))
    C,R=np.meshgrid(cc,rr);lo,la=inv.transform(xs[C]*h,ys[R]*h);inside=contains_xy(geom,lo,la)
    return R[inside].astype('int32'),C[inside].astype('int32')
   rows,cols=select(2);er,ec=select(8);assert np.array_equal(rows,er) and np.array_equal(cols,ec),(name,city.uc_id,unit,'padding failed')
   C,R=np.meshgrid(np.arange(max(0,c-35),min(len(xs),c+36)),np.arange(max(0,r-35),min(len(ys),r+36)))
   lo,la=inv.transform(xs[C]*h,ys[R]*h);inside=contains_xy(geom,lo,la);orr=R[inside].astype('int32');occ=C[inside].astype('int32')
   changed=not(np.array_equal(rows,orr) and np.array_equal(cols,occ));masks[(city.uc_id,unit)]=(rows,cols)
   for prefix,a in [('',rows),('old_',orr)]:arrays[f'{prefix}{city.uc_id}_{unit}_rows']=a
   for prefix,a in [('',cols),('old_',occ)]:arrays[f'{prefix}{city.uc_id}_{unit}_cols']=a
   audit.append(dict(dataset=name,uc_id=city.uc_id,unit=unit,old_n=len(orr),full_n=len(rows),changed=changed,
                     full_mask_sha256=hashlib.sha256(rows.tobytes()+cols.tobytes()).hexdigest(),old_mask_sha256=hashlib.sha256(orr.tobytes()+occ.tobytes()).hexdigest(),padding2_equals_padding8=True))
 np.savez_compressed(B/'masks'/f'{name}.npz',**arrays);pd.DataFrame(audit).to_csv(B/'masks'/f'{name}.csv',index=False)
 (B/'grid_catalog'/f'{name}.json').write_text(json.dumps(meta,indent=2));np.savez_compressed(B/'grid_catalog'/f'{name}_axes.npz',x=xs,y=ys)
 return masks,pd.DataFrame(audit),signature(xs,ys,meta)

SUN_CACHE={}
def sunset(lat,lon,day):
 k=(float(lat),float(lon),str(day))
 if k not in SUN_CACHE:
  tz=timezone(timedelta(minutes=float(lon)*4));s=sun(Observer(lat,lon),date=day,tzinfo=tz)['sunset'].astimezone(UTC);assert s.astimezone(tz).date()==day
  SUN_CACHE[k]=s
 return SUN_CACHE[k]
def requests_for(cities,intervals):
 records=[]
 for it in intervals.itertuples(index=False):
  for day in pd.date_range(it.start_date,periods=8):
   for c in cities.itertuples(index=False):
    s=sunset(c.lat,c.lon,day.date())
    for h in range(-3,7):
     t=(s+timedelta(hours=h,minutes=30)).replace(minute=0,second=0,microsecond=0)
     records.append(dict(uc_id=c.uc_id,event_year=int(it.year),event_step8=int(it.step8),event_time_id=int(it.time_id),local_date=str(day.date()),sunset_utc=s.isoformat(),target_hour_from_sunset=h,file_time_utc=t.isoformat(),file_year=t.year,file_doy=t.timetuple().tm_yday,file_hour=t.hour))
 return pd.DataFrame(records)
def listing(bucket,year,doy):
 import xml.etree.ElementTree as ET
 p=B/'raw/inventory'/bucket/f'{year}_{doy:03}.xml';p.parent.mkdir(exist_ok=True,parents=True)
 if p.exists():body=p.read_bytes()
 else:
  for attempt in range(4):
   try:
    r=session().get(f'https://{bucket}.s3.amazonaws.com/',params={'list-type':'2','prefix':f'ABI-L2-LSTC/{year}/{doy:03}/','max-keys':1000},timeout=(15,60));r.raise_for_status();body=r.content;p.write_bytes(body);p.chmod(0o444);break
   except Exception:
    if attempt==3:raise
    time.sleep(2)
 root=ET.fromstring(body);ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'};assert root.findtext('s:IsTruncated',namespaces=ns)=='false'
 keys=[k.text for k in root.findall('.//s:Contents/s:Key',ns)]
 log('inventory.jsonl',dict(bucket=bucket,year=year,doy=doy,path=p,sha256=sha(p),object_count=len(keys)))
 return [dict(file_year=year,file_doy=doy,file_hour=int(k.split('/')[3]),key=k) for k in keys]
def copy_meta(src,dst,ids,intervals):
 dst.mkdir(exist_ok=True)
 for p in src.iterdir():
  if p.suffix=='.csv':
   f=pd.read_csv(p,dtype={'uc_id':str})
   if 'uc_id' in f:f=f[f.uc_id.isin(ids)]
   if 'intervals' in p.name:
    # Preserve semantic aliases (e.g.2018–21) as an empty scoped view rather
    # than putting2022–24 dates in a filename that names a different period.
    f=f[f.time_id.isin(intervals.time_id)] if 'time_id' in f else intervals.copy()
   f.to_csv(dst/p.name,index=False)
  elif p.suffix in ['.json','.geojson','.md']:shutil.copyfile(p,dst/p.name)
 # Canonical aliases needed by downstream raw→analysis.
 intervals.to_csv(dst/'goes_sunset_intervals.csv',index=False)
def candidate_metadata(name,subset):
 src=SCI/name;ref=SCI/(subset or name)
 cf=next((ref/n for n in ['goes_sunset_cities.csv','goes18_2025_cities.csv','goes19_2025_cities.csv'] if (ref/n).exists()),None)
 assert cf,ref
 cities=pd.read_csv(cf,dtype={'uc_id':str})
 it=next((ref/n for n in ['goes_sunset_intervals.csv','goes18_2025_intervals.csv','goes19_2025_intervals.csv'] if (ref/n).exists()),None)
 intervals=pd.read_csv(it)
 return src,cities,intervals
def extract_one(name,bucket,key,requests_frame,masks,expected_signature,prefetch=None):
 part=B/'parts'/name/(hashlib.sha256(key.encode()).hexdigest()[:20]+'.parquet');part.parent.mkdir(exist_ok=True)
 if part.exists():return pd.read_parquet(part)
 p=prefetch.result() if prefetch is not None else raw(bucket,key);xs,ys,meta=grid(p)
 assert signature(xs,ys,meta)==expected_signature,(bucket,key,'nativegrid signature differs')
 with h5netcdf.File(p,'r',phony_dims='sort') as d:
  v=d.variables['LST'];packed=np.asarray(v[:]);a=v.attrs
  if str(safe(a.get('_Unsigned','false'))).lower()=='true' and packed.dtype.kind=='i':
   val=packed.view(np.dtype('u'+str(packed.dtype.itemsize)));fill=np.asarray(a['_FillValue'],dtype=packed.dtype).view(val.dtype).item()
  else:val=packed;fill=a['_FillValue']
  # Preserve original LST arithmetic; coordinates alone are evaluated in float64.
  lst=val.astype('float32')*float(a['scale_factor'])+float(a['add_offset']);lst[val==fill]=np.nan
  qv=d.variables['DQF'];dq=np.asarray(qv[:]);qa=qv.attrs
  if str(safe(qa.get('_Unsigned','false'))).lower()=='true' and dq.dtype.kind=='i':dq=dq.view(np.dtype('u'+str(dq.dtype.itemsize)))
  t=pd.Timestamp(safe(d.attrs['time_coverage_start']))
 rows=[]
 for req in requests_frame.to_dict('records'):
  row={c:req[c] for c in BASECOLS[:7]};row.update(scan_time_utc=t.isoformat(),actual_hour_from_sunset=(t-pd.Timestamp(req['sunset_utc'])).total_seconds()/3600,source_key=key)
  for u in ['core','ring']:
   rr,cc=masks[(req['uc_id'],u)];vv=lst[rr,cc];qq=dq[rr,cc]
   for label,ok in [('strict',qq==0),('recommended',qq<=1)]:
    sel=vv[ok&np.isfinite(vv)];row[f'{u}_{label}_count']=len(sel);row[f'{u}_{label}_lst_k']=float(sel.mean()) if len(sel) else np.nan
  rows.append(row)
 out=pd.DataFrame(rows);out.to_parquet(part,index=False);return out

def run_dataset(name,platform,subset,prepare_only=False):
 started=time.time();src,cities,intervals=candidate_metadata(name,subset);bucket=f'noaa-goes{platform}';dst=B/'corrected_data'/name
 # Original candidate metadata frompairedG18definesfullcohortforG16/G19sources.
 ids=set(cities.uc_id);copy_meta(src,dst,ids,intervals);cities.to_csv(dst/'goes_sunset_cities.csv',index=False)
 original_path=src/'goes_sunset_hourly.parquet';old=pd.read_parquet(original_path);old.uc_id=old.uc_id.astype(str);old=old[old.uc_id.isin(ids)].copy()
 sourcehash=sha(original_path);log('source_inputs.jsonl',dict(dataset=name,path=original_path,sha256=sourcehash))
 geo=json.loads((src/'goes_city_units.geojson').read_text());geoms={(str(x['properties']['uc_id']),x['properties']['unit']):shape(x['geometry']) for x in geo['features']}
 assert all((i,u) in geoms for i in ids for u in ['core','ring'])
 # Every original dataset usedonefixedgridprototype; audit per-year representatives too.
 first=old.source_key.iloc[0];p=raw(bucket,first);masks,audit,sig=masks_for(name,cities,geoms,p)
 grid_samples=[]
 for year,g in old.groupby('event_year'):
  for key in [g.source_key.min(),g.source_key.max()]:
   fp=raw(bucket,key);gx,gy,gm=grid(fp);ss=signature(gx,gy,gm);assert ss==sig,(name,year,key,'sample grid differs');grid_samples.append(dict(key=key,path=str(fp),sha256=sha(fp),signature=ss))
 (B/'grid_catalog'/f'{name}_year_controls.json').write_text(json.dumps(grid_samples,indent=2))
 eligible=audit.pivot(index='uc_id',columns='unit',values='full_n');eligible_ids=set(eligible[(eligible.core>=3)&(eligible.ring>=10)].index)
 affected=set(audit[audit.changed].uc_id)
 req=requests_for(cities,intervals);req['geometric_eligible']=req.uc_id.isin(eligible_ids)
 inv=pd.read_csv(src/'goes_lstc_key_inventory.csv').rename(columns={'year':'file_year','doy':'file_doy','hour':'file_hour'})[['file_year','file_doy','file_hour','key']].drop_duplicates(['file_year','file_doy','file_hour'],keep='last')
 req=req.merge(inv,on=['file_year','file_doy','file_hour'],how='left',validate='many_to_one')
 # Refresh archive daysfor allmissingkeys,includingentire absentdays; never fallback toanotherhour.
 missing=req[req.key.isna()&req.geometric_eligible][['file_year','file_doy']].drop_duplicates();newkeys=[]
 with ThreadPoolExecutor(max_workers=2) as pool:
  fs=[pool.submit(listing,bucket,int(r.file_year),int(r.file_doy)) for r in missing.itertuples(index=False)]
  for f in as_completed(fs):newkeys.extend(f.result())
 if newkeys:
  inv=pd.concat([inv,pd.DataFrame(newkeys)],ignore_index=True).drop_duplicates(['file_year','file_doy','file_hour'],keep='last')
  req=req.drop(columns='key').merge(inv,on=['file_year','file_doy','file_hour'],how='left',validate='many_to_one')
 inv.to_csv(dst/'goes_lstc_key_inventory.csv',index=False)
 req['archive_present']=req.key.notna();req.to_parquet(dst/'repair_all_requests.parquet',index=False);req[~req.archive_present].to_csv(dst/'repair_missing_requests.csv',index=False)
 used=req[req.geometric_eligible&req.archive_present].copy()
 # Establish true datesfromphysicalsunset timestamp; rejecttheinheriteddateasgroundtruth.
 lon=old.uc_id.map(cities.set_index('uc_id').lon);actual=(pd.to_datetime(old.sunset_utc,utc=True,format='mixed')+pd.to_timedelta(lon*4,unit='m')).dt.strftime('%Y-%m-%d')
 assert actual.eq((pd.to_datetime(old.local_date)-pd.Timedelta(days=1)).dt.strftime('%Y-%m-%d')).all()
 old['old_labeled_local_date']=old.local_date;old['local_date']=actual
 K=['uc_id','local_date','target_hour_from_sunset'];assert not old.duplicated(K).any(),(name,'old duplicate')
 cols=K+['source_key','sunset_utc','scan_time_utc','actual_hour_from_sunset',*REGCOLS]
 joined=used.merge(old[cols],on=K,how='left',suffixes=('','_old'),validate='one_to_one')
 reuse=joined.source_key.notna()&joined.source_key.eq(joined.key)&~joined.uc_id.isin(affected)
 dt=(pd.to_datetime(joined.loc[reuse,'sunset_utc'],utc=True,format='mixed')-pd.to_datetime(joined.loc[reuse,'sunset_utc_old'],utc=True,format='mixed')).dt.total_seconds().abs();assert dt.max()<1e-5
 assert len(joined)==len(used)
 plan=dict(dataset=name,bucket=bucket,candidate_cities=len(cities),geometric_eligible_cities=len(eligible_ids),affected_city_ids=sorted(affected),
           requested_rows=len(req),archive_missing_rows=int((~req.archive_present&req.geometric_eligible).sum()),available_eligible_rows=len(used),
           reusable_rows=int(reuse.sum()),native_reextract_rows=int((~reuse).sum()),native_reextract_objects=int(joined.loc[~reuse,'key'].nunique()),
           original_input_sha256=sourcehash,prototype_grid_signature=sig,calendar='Astral intended local-sunset date; longitude-based fixed solar offset, UTC conversion',
           spatial='complete saved polygons, boundary vertices densified0.005degree,2nativepixelpaddingverifiedagainst8pixelpadding',
           arithmetic='Originalfloat32LSTdecodeandmean;float64nativecoordinates;originalquality0and<=1andthresholdsunchanged')
 (dst/'repair_plan.json').write_text(json.dumps(plan,indent=2));print('PLAN',json.dumps(plan),flush=True)
 # Readiness plan is written even if native acquisitionlaterfails.
 if prepare_only:return plan
 oldrows=joined.loc[reuse,BASECOLS+REGCOLS].copy()
 extraction_requests=used.merge(joined.loc[~reuse,K],on=K,validate='one_to_one')
 rows=[];tasks=list(extraction_requests.groupby('key',sort=True));count=0
 # Network latency dominates. Four file fetchers return only paths; two decoders
 # bound active array memory. Future results retain no downloaded byte buffers.
 with ThreadPoolExecutor(max_workers=4) as fetchers, ThreadPoolExecutor(max_workers=2) as pool:
  prefetched={key:fetchers.submit(raw,bucket,key) for key,g in tasks}
  futures={pool.submit(extract_one,name,bucket,key,g,masks,sig,prefetched[key]):key for key,g in tasks}
  for future in as_completed(futures):
   try:rows.append(future.result())
   except Exception:
    log('extraction_failures.jsonl',dict(dataset=name,key=futures[future],error=traceback.format_exc()));raise
   count+=1
   if count%50==0 or count==len(tasks):print('NATIVE',name,count,'/',len(tasks),'elapsed',round(time.time()-started,1),flush=True)
 native=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame(columns=BASECOLS+REGCOLS)
 out=pd.concat([oldrows,native],ignore_index=True)[BASECOLS+REGCOLS].sort_values(['event_time_id','uc_id','local_date','target_hour_from_sunset']).reset_index(drop=True)
 assert len(out)==len(used) and not out.duplicated(['uc_id','event_time_id','local_date','target_hour_from_sunset']).any()
 out.to_parquet(dst/'goes_sunset_hourly.parquet',index=False)
 provenance=used[BASECOLS[:7]+['key']].merge(joined.loc[reuse,K].assign(provenance_type='calendar_remap_exact_native_mask'),on=K,how='left',validate='one_to_one')
 provenance.provenance_type=provenance.provenance_type.fillna('native_reextraction_complete_polygon_or_missing_day');provenance.to_parquet(dst/'repair_observation_provenance.parquet',index=False)
 audit[['uc_id','unit','full_n']].rename(columns={'full_n':'n_grid_pixels'}).to_csv(dst/'goes_city_grid_mask_summary.csv',index=False)
 assert sha(original_path)==sourcehash
 plan.update(status='COMPLETE',output_rows=len(out),output_sha256=sha(dst/'goes_sunset_hourly.parquet'),elapsed_seconds=time.time()-started,
             input_unchanged=True,source_keys_unaltered_on_reused_rows=True,reuse_sunset_max_error_seconds=float(dt.max()) if len(dt) else None)
 (dst/'repair_manifest.json').write_text(json.dumps(plan,indent=2));print('COMPLETE',name,len(out),round(time.time()-started,1),'seconds',flush=True)
 if 'external_metric' in name:
  ext=B/'corrected_external';ext.mkdir(exist_ok=True);alias=ext/f'GOES{platform}_sunset_hourly.parquet'
  if not alias.exists():os.link(dst/'goes_sunset_hourly.parquet',alias)
 return plan

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--datasets',nargs='*');ap.add_argument('--prepare-only',action='store_true');a=ap.parse_args()
 selected=[c for c in CONFIGS if not a.datasets or c[0] in a.datasets]
 outputs=[]
 for name,platform,subset in selected:
  manifest=B/'corrected_data'/name/'repair_manifest.json'
  if manifest.exists() and not a.prepare_only:
   outputs.append(json.loads(manifest.read_text()));print('EXISTING_COMPLETE',name,flush=True);continue
  outputs.append(run_dataset(name,platform,subset,a.prepare_only));(B/'extraction_progress.json').write_text(json.dumps(outputs,indent=2))
 print('ALL_SELECTED_COMPLETE',len(outputs),flush=True)
