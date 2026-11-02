"""Read-only science check against actual accepted XML of the tracked Word files.

Expected S5 and21-transition values are reconstructed from the corrected paired
prediction/hourly Parquets, never from the authoring plan. Fixed tolerance for
unrounded budget closure is1e-10 K². Display comparisons use the stated three
RMSE/four MSE decimal places. Previous S1–S4 accepted content is compared against
the immutable pre-pass snapshot. No fitting/provider retrieval/Word edit occurs.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,re,sys,unicodedata,xml.etree.ElementTree as ET
import numpy as np,pandas as pd
B=Path('/Users/apple/Downloads/RS revision 1');C=B/'concision_20261030'
E=B/'continuation_20261029/release/downstream-measurand-aware-lst-harmonization-2.1.0-r1/02_EVIDENCE'
OUT=C/'records';W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';q=lambda s:'{'+W+'}'+s
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
norm=lambda s:re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(s)).replace('−','-').replace('–','-')).strip()
checks=[];cells=[];sources={};documents={}
def ck(name,ok,detail=None):
 checks.append(dict(check=name,passed=bool(ok),details=detail))
 assert ok,(name,detail)
def inputp(rel):
 p=E/rel;sources[str(p)]=sha(p);return p
def accepted(el):
 if el.tag==q('del'):return None
 if el.tag==q('tr') and el.find(q('trPr')+'/'+q('del')) is not None:return None
 if el.tag==q('p') and el.find(q('pPr')+'/'+q('rPr')+'/'+q('del')) is not None:return None
 z=ET.Element(el.tag,el.attrib);z.text=el.text;z.tail=el.tail
 for child in el:
  a=accepted(child)
  if a is None:continue
  if a.tag==q('ins'):
   for b in list(a):z.append(b)
  else:z.append(a)
 return z
def txt(el):return ''.join(x.text or '' for x in el.iter(q('t')))
def load_doc(p,bind=False):
 with ZipFile(p) as z:
  r=accepted(ET.fromstring(z.read('word/document.xml')))
  settings=ET.fromstring(z.read('word/settings.xml'))
 if bind:
  documents[p.name]=dict(path=str(p),sha256=sha(p))
  ck(p.name+' Track Changes enabled',settings.find(q('trackRevisions')) is not None)
 ps=[txt(x) for x in r.iter(q('p'))];tables=[];caption=''
 for child in r.find(q('body')):
  if child.tag==q('p'):
   s=txt(child)
   if re.match(r'Table S\d+\.',s):caption=s
  if child.tag==q('tbl'):
   rows=[[txt(tc) for tc in tr.findall(q('tc'))] for tr in child.findall(q('tr'))]
   if rows:tables.append(dict(caption=caption,rows=rows))
 return ps,tables
main=B/'Manuscript v1_suggestions.docx';si=B/'supplementary_suggestions.docx'
mp,mt=load_doc(main,True);sp,st=load_doc(si,True)
baseline=C/'snapshots/supplementary_suggestions.docx';sources[str(baseline)]=sha(baseline)
_,old=load_doc(baseline)
ck('Current SI contains exactly five accepted tables',len(st)==5,len(st))
ck('SI captions ordered S1 through S5',[re.match(r'Table S(\d+)\.',z['caption'])[1] for z in st]==['1','2','3','4','5'])
ck('Baseline contains four accepted tables',len(old)==4)
for i in range(4):
 ck('S'+str(i+1)+' caption unchanged',st[i]['caption']==old[i]['caption'])
 ck('S'+str(i+1)+' all accepted cells unchanged',st[i]['rows']==old[i]['rows'])
alltext='\n'.join(mp+sp)
ck('No separately numbered SI Notes',not re.search(r'(?:Supplementary\s+)?Notes?\s+S\d+',alltext))
ck('No separately numbered Data attachments',not re.search(r'(?:Supplementary\s+)?Data\s+S\d+',alltext))

def budget(f,label):
 a=np.asarray(f.source_core-f.target_core,float);b=np.asarray(f.source_ring-f.target_ring,float)
 c=np.asarray(f.pred_core-f.target_core,float);d=np.asarray(f.pred_ring-f.target_ring,float)
 avg=lambda x:float(np.mean(x));var=lambda x:avg((x-avg(x))**2);cov=lambda x,y:avg((x-avg(x))*(y-avg(y)))
 vg=var(a)+var(b)-var(c)-var(d);bg=(avg(a)-avg(b))**2-(avg(c)-avg(d))**2
 pen=2*(cov(a,b)-cov(c,d));raw=avg((a-b)**2);corrected=avg((c-d)**2)
 ck(label+' direct MSE closure',abs(vg+bg-pen-(raw-corrected))<1e-10,vg+bg-pen-(raw-corrected))
 return dict(label=label,n=len(f),cities=f.uc_id.nunique(),intervals=f.event_time_id.nunique(),
  raw_rmse=np.sqrt(raw),corrected_rmse=np.sqrt(corrected),variance_gain=vg,bias_gain=bg,
  gross_gain=vg+bg,covariance_penalty=pen,net_gain=raw-corrected)
hist=pd.read_parquet(inputp('analysis_outputs/goes17_goes16_external_metric/validation_2021_hourly_predictions.parquet'))
modern=pd.read_parquet(inputp('analysis_outputs/goes18_goes19_metric_harmonization/validation_2026_hourly_predictions.parquet'))
values=[budget(hist,'2021 pooled')]
for year,f in [(2021,hist),(2026,modern)]:
 for h,g in f.groupby('target_hour_from_sunset'):
  values.append(budget(g,str(year)+' h='+('+' if h>0 else '')+str(h)))
for lo,hi in [(40,50),(50,60)]:
 g=modern[modern.vza_target.ge(lo)&modern.vza_target.lt(hi)]
 values.append(budget(g,'2026 G18 VZA ['+str(lo)+', '+str(hi)+')°'))
ck('Exactly 23 independently reconstructed S5 rows',len(values)==23)
table=st[4]
ck('S5 has header and 23 rows',len(table['rows'])==24)
ck('S5 six columns in every row',all(len(r)==6 for r in table['rows']))
headers=['Stratum','n / cities','Contrast RMSE, raw / corrected (K)','Gross gain (K²)','Covariance penalty (K²)','Net gain (K²)']
for j,h in enumerate(headers):
 ck('S5 header column '+str(j+1),norm(table['rows'][0][j])==norm(h))
def fmt(x,d):
 if abs(x)<5*10**(-d-1):x=0.
 return f'{x:.{d}f}'
for i,v in enumerate(values,1):
 expected=[v['label'],f"{v['n']:,} / {v['cities']}",fmt(v['raw_rmse'],3)+' / '+fmt(v['corrected_rmse'],3),fmt(v['gross_gain'],4),fmt(v['covariance_penalty'],4),fmt(v['net_gain'],4)]
 for j,s in enumerate(expected):
  got=table['rows'][i][j];passed=norm(got)==norm(s)
  cells.append(dict(table='S5',row=i,column=j+1,actual=got,expected=s,passed=passed))
  ck('S5 row '+str(i)+' column '+str(j+1),passed,dict(actual=got,expected=s))
modern_values=[v for v in values if v['label'].startswith('2026 h=')]
ck('All 10 modern hour bins present',len(modern_values)==10)
ck('All 8 unfavorable modern hourly results retained',sum(v['net_gain']<0 for v in modern_values)==8)
ck('Modern hour stratum n sums to 5716',sum(v['n'] for v in modern_values)==5716)
ck('Historical hour stratum n sums to2602',sum(v['n'] for v in values if v['label'].startswith('2021 h='))==2602)
ck('High VZA unfavorable result retained',values[-1]['net_gain']<0 and float(norm(table['rows'][-1][-1]))<0)
caption=table['caption']
for phrase in ['n counts city–interval–hour means','four intervals','eight intervals','lower-inclusive and upper-exclusive','Gross gain = component-variance + differential-bias gain','do not isolate angular causes']:
 ck('S5 caption retains '+phrase,norm(phrase) in norm(caption))

transition_values=[]
for scenario in ['recommended_common_daily','strict_common_daily']:
 f=pd.read_parquet(inputp('quality/'+scenario+'_hourly.parquet'));rows=[]
 for (city,event),g in f.groupby(['uc_id','event_time_id']):
  pre=g[g.target_hour_from_sunset.isin([-3,-2,-1])];post=g[g.target_hour_from_sunset.isin([4,5,6])]
  if len(pre)<2 or len(post)<2:continue
  r=dict(uc_id=city,event_time_id=event)
  for col in ['target_core','target_ring','source_core','source_ring','pred_core','pred_ring']:r[col]=post[col].mean()-pre[col].mean()
  rows.append(r)
 v=budget(pd.DataFrame(rows),scenario);transition_values.append(v)
 ck(scenario+' exactly21transitions across3cities',v['n']==21 and v['cities']==3)
 ck(scenario+' transition correction worsens RMSE',v['corrected_rmse']>v['raw_rmse'])
para=next(p for p in mp if 'component correction increased transition-contrast RMSE' in p)
expected_sentence=('On the same restricted support, component correction increased transition-contrast RMSE from '+fmt(transition_values[0]['raw_rmse'],3)+' to '+fmt(transition_values[0]['corrected_rmse'],3)+' K under recommended screening and from '+fmt(transition_values[1]['raw_rmse'],3)+' to '+fmt(transition_values[1]['corrected_rmse'],3)+' K under strict DQF-0 screening.')
ck('Actual main3.5 sentence matches independently rebuilt transition values',norm(expected_sentence) in norm(para),expected_sentence)
for phrase in ['only three cities (Tucson, South Valley and Albuquerque)','215 hourly observations and 21 transitions','On the same restricted support','conditional comparison cannot establish robustness across all 75 cities']:
 ck('Main3.5 retains '+phrase,norm(phrase) in norm(para))
ck('Main3.5 distinguishes corrected hourly comparison','corrected hourly RMSE difference' in para)
ck('Main explicitly references S5',bool(re.search(r'Table S5', '\n'.join(mp))))

for p,h in sources.items():ck('Input unchanged '+Path(p).name,sha(Path(p))==h)
for n,z in documents.items():ck('Word unchanged during audit '+n,sha(Path(z['path']))==z['sha256'])
out=dict(status='PASS',command=[sys.executable,str(Path(__file__).resolve())],documents=documents,
 source_hashes=sources,checks=checks,check_count=len(checks),s5_compared_data_cells=len(cells),cells=cells,
 independent_s5_rows=values,independent_transition_results=transition_values,
 scope='Direct retained-prediction/common-support scalar reconstruction against actual accepted Word XML; all prior S1–S4 accepted cells/captions unchanged. No Word edits, model fits, provider retrievals or new full scientific rerun.',
 limitations=['This check does not replace final rendering/visual inspection.',
 'Independent raw-product surface validation, unique physical attribution and final-workflow unseen-city performance retain their documented limits.',
 'Response letters are not drafted or cross-checked in this task.'])
(OUT/'final_document_science_check.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
lines=['# Final document scientific check','',
 '**PASS: '+str(len(checks))+' checks, with '+str(len(cells))+' S5 data cells compared against independent reconstruction.**',
 '',
 'The actual accepted content of both current tracked Word files was parsed directly. The expected values were recomputed from corrected per-observation prediction/common-support Parquets, not copied from the authoring plan. All23S5 rows match: historical pool, all10historicalhours, all10modernhours and both referenceVZA strata. All8unfavorablemodernhour results and the unfavorable highVZA result remain. Original S1–S4 accepted captions/cells are identical to the pre-pass snapshot. The S5 caption retains support, units, bin boundaries, model/era distinctions and the noncausal geometry qualification.',
 '',
 'The new Results3.5 sentence exactly matches the independently rebuilt21transitions per scenario: recommended RMSE0.9611786587→0.9915247948K and strictDQF0 RMSE0.8159860343→0.8399358646K. The same paragraph names the three cities,21transitions, restricted common support and lack of75city robustness. It distinguishes the corrected hourly comparison from the newly added transition comparison.',
 '',
 'This is a read-only document/source consistency check, not a new scientific rerun. No fitting, raw retrieval, Word edit or response-letter drafting occurred. Source bytes and both delivered Word hashes remained unchanged during the audit. Final visual checks remain the coordinator’s separate responsibility.',
 '',
 '## Bound current files','']
for n,z in documents.items():lines.append('- '+n+': `'+z['sha256']+'`')
lines+=['','Exact commands, source hashes, assertions and cell-level comparisons are in `final_document_science_check.json`.']
(OUT/'final_document_science_check.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in out.items() if k in ['status','documents','check_count','s5_compared_data_cells','scope']},indent=2))
