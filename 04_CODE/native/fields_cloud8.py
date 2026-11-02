from pathlib import Path
import os
PACKAGE_ROOT=Path(__file__).resolve().parents[2]
NATIVE_WORKSPACE=Path(os.environ.get("LST_NATIVE_WORKSPACE",str(PACKAGE_ROOT/"data/native_workspace"))).resolve()
import json,hashlib,sys,re,xml.etree.ElementTree as ET
import numpy as np,pandas as pd,h5netcdf,requests
from scipy.ndimage import binary_dilation
from pyproj import CRS,Transformer
from shapely.geometry import shape
from shapely import contains_xy
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from native_audit import getpath,conv
B=NATIVE_WORKSPACE/'auxiliary/native/cloud8';S=Path(os.environ.get('LST_REPRODUCTION_OUTPUT',str(PACKAGE_ROOT/'outputs/reproduced')))/'repaired';META=PACKAGE_ROOT/'02_EVIDENCE/si_tables/fixed_city_candidate_metadata.csv'
allmeta=json.loads((B.parent/'results/cloud8_audit_summary.json').read_text())['files'];scenes=[r for r in allmeta if '_2026_Phoenix_' in r['label']];scenes.sort(key=lambda x:(x['target_hour'],x['bucket']))
assert len(scenes)==32
cities=pd.read_csv(META,dtype={'uc_id':str});newbase=pd.read_parquet(S/'outputs/grl_deepening_2026/goes18_goes19_metric_harmonization/validation_2026_hourly_predictions.parquet');newids=set(newbase.uc_id.astype(str));cities=cities[cities.uc_id.isin(newids)].copy();assert len(cities)==len(newids);geoj=json.loads((S/'data/goes18_2026_metric_holdout/goes_city_units.geojson').read_text());geoms={(str(x['properties']['uc_id']),x['properties']['unit']):shape(x['geometry']) for x in geoj['features']}
for s in scenes:assert s['key'].startswith('ABI-L2-LSTC/2026/')

def decode(p):
 with h5netcdf.File(p,'r',phony_dims='sort') as d:
  v=d.variables['LST'];a=v.attrs;raw=np.asarray(v[:]);unsigned=str(a.get('_Unsigned','false')).lower()=='true'
  raw=raw.view(np.dtype('u'+str(raw.dtype.itemsize))) if unsigned and raw.dtype.kind=='i' else raw
  fill=np.asarray(a['_FillValue'],dtype=v.dtype).view(raw.dtype).item()
  lst=raw.astype(float)*float(a['scale_factor'])+float(a['add_offset']);lst[raw==fill]=np.nan
  dqf=np.asarray(d.variables['DQF'][:]);pqi=np.asarray(d.variables['PQI'][:]);xv=d.variables['x'];yv=d.variables['y']
  x=np.asarray(xv[:],float)*float(xv.attrs.get('scale_factor',1))+float(xv.attrs.get('add_offset',0));y=np.asarray(yv[:],float)*float(yv.attrs.get('scale_factor',1))+float(yv.attrs.get('add_offset',0));proj=conv(dict(d.variables['goes_imager_projection'].attrs))
 h=float(proj['perspective_point_height']);crs=CRS.from_proj4(f"+proj=geos +h={h} +lon_0={float(proj['longitude_of_projection_origin'])} +sweep={proj.get('sweep_angle_axis','x')} +a={float(proj['semi_major_axis'])} +b={float(proj['semi_minor_axis'])} +units=m")
 fwd=Transformer.from_crs('EPSG:4326',crs,always_xy=True);inv=Transformer.from_crs(crs,'EPSG:4326',always_xy=True)
 return dict(lst=lst,dqf=dqf,pqi=pqi,x=x,y=y,h=h,fwd=fwd,inv=inv,shape=lst.shape)

def maskcoords(g,city):
 # Conservative projected bounds of the entire geographic polygon envelope.
 bounds=geoms[(city.uc_id,'core')].union(geoms[(city.uc_id,'ring')]).bounds
 left,bottom,right,top=g['fwd'].transform_bounds(*bounds,densify_pts=101)
 assert np.isfinite([left,bottom,right,top]).all(),(city.uc_id,bounds)
 xx=np.where((g['x']>=left/g['h'])&(g['x']<=right/g['h']))[0]
 yy=np.where((g['y']>=bottom/g['h'])&(g['y']<=top/g['h']))[0]
 assert len(xx)>0 and len(yy)>0,city.uc_id
 cc=np.arange(max(0,xx.min()-3),min(g['shape'][1],xx.max()+4));rr=np.arange(max(0,yy.min()-3),min(g['shape'][0],yy.max()+4))
 C,R=np.meshgrid(cc,rr);lon,lat=g['inv'].transform(g['x'][C]*g['h'],g['y'][R]*g['h'])
 return R,C,lon,lat

def fetch_acm(s):
 # The native LST provenance names the exact companionACM scan; acquirethatfilewiththematchingstartandend timestamp.
 attrs=s['variables']['algorithm_dynamic_input_data_container']['attrs'];templ=attrs.get('input_ABI_L2_4_level_cloud_mask_data');assert templ and templ!='null'
 key=s['key'];prefix='/'.join(key.split('/')[:4]).replace('ABI-L2-LSTC','ABI-L2-ACMC')+'/'
 r=requests.get(f"https://{s['bucket']}.s3.amazonaws.com/",params={'list-type':'2','prefix':prefix},timeout=(15,60));r.raise_for_status();root=ET.fromstring(r.content);ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'};keys=[x.text for x in root.findall('.//s:Key',ns)];start=re.search(r'_s(\d+)_e',key).group(1);matches=[k for k in keys if '_s'+start+'_e' in k];assert matches,(s['bucket'],prefix,start)
 p=getpath(s['bucket'],matches[0]);
 with h5netcdf.File(p,'r',phony_dims='sort') as d:
  vn=next(n for n in ['ACM','BCM','CloudMask'] if n in d.variables);a=np.asarray(d.variables[vn][:]);attrs0=conv(dict(d.variables[vn].attrs));coords=[]
  for n in ['x','y']:
   v=d.variables[n];coords.append(np.asarray(v[:],float)*float(v.attrs.get('scale_factor',1))+float(v.attrs.get('add_offset',0)))
  t=conv(dict(d.attrs));projection=conv(dict(d.variables['goes_imager_projection'].attrs))
 return a,coords,dict(path=str(p),key=matches[0],variable=vn,attrs=attrs0,projection=projection,global_attributes=t,sha256=hashlib.sha256(p.read_bytes()).hexdigest())

rows=[];scene_stats=[];acm_metadata=[];sample_arrays={};replay=[];pqidetails=[]
for s in scenes:
 g=decode(s['path']);dqi=g['dqf'];pqi=g['pqi'];valid=(dqi<=1)&np.isfinite(g['lst'])&(g['lst']>=180)&(g['lst']<=380)
 # NativePQIcloud classes: 0clear,4probablyclear,8probablycloudy,12cloudy.
 cloud=(pqi&12);clearpqi=cloud==0;badcloud=(cloud>=8)|(pqi==65535)
 masks={'recommended':valid,'strict_DQF0':valid&(dqi==0),'PQI_clear':valid&clearpqi,'PQI_clear_buffer1':valid&clearpqi&~binary_dilation(badcloud,iterations=1),'PQI_clear_buffer2':valid&clearpqi&~binary_dilation(badcloud,iterations=2)}
 try:
  acm,co,amd=fetch_acm(s);amd['scene_label']=s['label'];acm_metadata.append(amd)
  assert acm.shape==g['shape'],(acm.shape,g['shape']);assert np.max(abs(co[0]-g['x']))<1e-7 and np.max(abs(co[1]-g['y']))<1e-7
  aclear=acm==0;acloud=(acm>=2);masks['ACM_clear']=valid&aclear;masks['ACM_clear_buffer1']=valid&aclear&~binary_dilation(acloud,iterations=1);masks['ACM_clear_buffer2']=valid&aclear&~binary_dilation(acloud,iterations=2)
  scene_stats.append(dict(label=s['label'],ACM_available=True,clear_pqi_acm_disagreements=int((valid&(aclear!=clearpqi)).sum())))
 except Exception as e:
  scene_stats.append(dict(label=s['label'],ACM_available=False,ACM_error=repr(e)))
 # Detailednativequalityreasoncounts on every75retainedcitygeometry atthesescans,notwholeCONUS.
 for city in cities.itertuples(index=False):
  if (city.uc_id,'core') not in geoms:continue
  R,C,lon,lat=maskcoords(g,city)
  for unit in ['core','ring']:
   inside=contains_xy(geoms[(city.uc_id,unit)],lon,lat);rr=R[inside];cc=C[inside];n=len(rr)
   if not n:continue
   vals=g['lst'][rr,cc];q=dqi[rr,cc];pq=pqi[rr,cc];vv=valid[rr,cc]
   for label,mask in masks.items():
    use=mask[rr,cc];rows.append(dict(scene_label=s['label'],bucket=s['bucket'],source_key=s['key'],scan_time_utc=s['global']['time_coverage_start'],uc_id=city.uc_id,unit=unit,screen=label,grid_pixels=n,n=int(use.sum()),mean_K=float(vals[use].mean()) if use.any() else np.nan,sd_K=float(vals[use].std()) if use.any() else np.nan))
   for qa in [0,1]:
    use=vv&(q==qa);nq=int(use.sum())
    pqidetails.append(dict(scene_label=s['label'],uc_id=city.uc_id,unit=unit,DQF=qa,n=nq,large_view=int((use&((pq&2048)==2048)).sum()),other_emissivity=int((use&((pq&1024)==1024)).sum()),bad_aod=int((use&((pq&32)==32)).sum()),probably_clear=int((use&((pq&12)==4)).sum()),normal_input=int((use&((pq&16)==0)).sum()),very_dry=int((use&((pq&768)==0)).sum()),dry=int((use&((pq&768)==256)).sum()),moist=int((use&((pq&768)==512)).sum()),very_moist=int((use&((pq&768)==768)).sum())))
 # Phoenixnativepanel region: longitude−113.0..−111.4;latitude32.9..34.3; declarednotchosenbyresult.
 city=cities[cities.uc_id.eq('4699')].iloc[0];cx,cy=g['fwd'].transform(city.lon,city.lat);ri=int(np.argmin(abs(g['y']-cy/g['h'])));ci=int(np.argmin(abs(g['x']-cx/g['h'])));rr=np.arange(max(0,ri-85),min(g['shape'][0],ri+86));cc=np.arange(max(0,ci-85),min(g['shape'][1],ci+86));C,R=np.meshgrid(cc,rr);lon,lat=g['inv'].transform(g['x'][C]*g['h'],g['y'][R]*g['h']);v=np.where(valid[R,C],g['lst'][R,C],np.nan)
 sample_arrays[s['label']]={'lon':lon,'lat':lat,'lst':v,'scene':s}
 np.savez_compressed(B/'results'/f"{s['label']}_map_arrays.npz",lon=lon,lat=lat,lst=v)
 print('SCENE',s['label'],'valid',int(valid.sum()),'screens',list(masks),flush=True)
pd.DataFrame(rows).to_csv(B/'results/native_city_screening.csv',index=False);pd.DataFrame(pqidetails).to_csv(B/'results/native_PQI_reasons.csv',index=False);(B/'results/cloud_scene_status.json').write_text(json.dumps(scene_stats,indent=2));(B/'results/ACM_metadata.json').write_text(json.dumps(acm_metadata,indent=2))
# Validate regional means againstretainedextractsonsamegeometry/grid/sourcekey.
results=pd.DataFrame(rows)
for bucket,dirn in [('noaa-goes18','goes18_2026_metric_holdout'),('noaa-goes19','goes19_2026_metric_holdout')]:
 old=pd.read_parquet(S/'data'/dirn/'goes_sunset_hourly.parquet');old.uc_id=old.uc_id.astype(str)
 for unit in ['core','ring']:
  new=results[(results.bucket==bucket)&(results.unit==unit)&(results.screen=='recommended')];merged=new.merge(old,on=['uc_id','source_key'],validate='one_to_many');good=merged.n>0
  err=float(abs(merged.loc[good,'mean_K']-merged.loc[good,f'{unit}_recommended_lst_k']).max());replay.append(dict(bucket=bucket,unit=unit,matching_rows=len(merged),count_match=bool((merged.n==merged[f'{unit}_recommended_count']).all()),mean_max_abs_error_K=err));assert err<1e-3 and replay[-1]['count_match'],replay[-1]
(B/'results/native_region_replay.json').write_text(json.dumps(replay,indent=2))

print("DONE_CLOUD8",len(rows),"regionalrows",flush=True)
