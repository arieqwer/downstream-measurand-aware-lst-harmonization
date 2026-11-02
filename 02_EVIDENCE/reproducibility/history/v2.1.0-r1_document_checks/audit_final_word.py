"""Read-only independent check of final tracked Word's accepted content.

Expected values come from independently checked scientific data, never the
authoring plan. Run only after the coordinator finishes the current edit batch.
"""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import csv,hashlib,json,math,re,unicodedata
B=Path('/Users/apple/Downloads/RS revision 1');C=B/'continuation_20261029';O=C/'science/claims_audit';R=B/'repair_20261029';S=R/'pipeline/repaired/outputs/grl_deepening_2026'
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'};W=N['w'];q=lambda x:'{'+W+'}'+x
checks=[];cells=[];sources={};documents={}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
norm=lambda x:re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(x)).replace('−','-').replace('–','-')).strip()
def ck(name,ok,details=None):checks.append(dict(check=name,passed=bool(ok),details=details))
def readcsv(p):sources[str(p)]=sha(p);return list(csv.DictReader(p.open()))
def readjson(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
def text(p):return ''.join(p.xpath('.//w:t/text()',namespaces=N))
def resolve(root,accept):
 r=deepcopy(root)
 # Paragraph/row revision marks affect structure, before flattening text changes.
 remove='del' if accept else 'ins'
 for x in list(r.xpath('//w:tr[w:trPr/w:'+remove+']|//w:p[w:pPr/w:rPr/w:'+remove+']',namespaces=N)):
  if x.getparent() is not None:x.getparent().remove(x)
 for x in list(r.xpath('//w:'+remove,namespaces=N)):
  if x.getparent() is not None:x.getparent().remove(x)
 keep='ins' if accept else 'del'
 for x in reversed(r.xpath('//w:'+keep,namespaces=N)):
  parent=x.getparent()
  if parent is None:continue
  i=parent.index(x)
  for c in list(x):x.remove(c);parent.insert(i,c);i+=1
  parent.remove(x)
 for x in r.xpath('//w:delText',namespaces=N):x.tag=q('t')
 return r
def load_doc(name):
 p=B/name
 with ZipFile(p) as z:
  raw=E.fromstring(z.read('word/document.xml'));r=resolve(raw,True);ps=[text(x) for x in r.xpath('//w:body//w:p',namespaces=N)];rels={x.get('Id'):x.get('Target') for x in E.fromstring(z.read('word/_rels/document.xml.rels'))};images=[]
  for x in r.xpath('//a:blip',namespaces=N):images.append(hashlib.sha256(z.read('word/'+rels[x.get('{'+N['r']+'}embed')])).hexdigest())
  tables=[];caption=''
  for child in r.find(q('body')):
   if child.tag==q('p'):
    t=text(child)
    if re.match(r'Table S?\d+\.',t):caption=t
   if child.tag==q('tbl'):
    rows=[[' '.join(text(p) for p in tc.findall(q('p'))) for tc in tr.findall(q('tc'))] for tr in child.findall(q('tr'))]
    # Word retains table containers whose every row is a tracked deletion. They
    # have no accepted content and must not count as accepted scientific tables.
    if rows:tables.append(dict(caption=caption,rows=rows))
  settings=E.fromstring(z.read('word/settings.xml'));ck(name+' tracking enabled',settings.find(q('trackRevisions')) is not None)
  documents[name]=dict(path=str(p),sha256=sha(p),paragraphs=ps,tables=tables,accepted_images=images)
  (O/(Path(name).stem+'_final_accepted.txt')).write_text('\n'.join('P'+str(i)+': '+t for i,t in enumerate(ps)))
  return raw,r,ps,tables,images
mraw,mr,mp,mt,images=load_doc('Manuscript v1_suggestions.docx');sraw,sr,sp,st,si_images=load_doc('supplementary_suggestions.docx');m='\n'.join(mp);s='\n'.join(sp)
baseline=readjson(C/'records/baseline_manifest.json')
for row in baseline:
 if 'suggestions' not in row['path']:ck('Original immutable '+Path(row['path']).name,sha(Path(row['path']))==row['sha256'])

for name,raw,accepted,original in [('Main',mraw,mr,'Manuscript v1.docx'),('SI',sraw,sr,'supplementary.docx')]:
 with ZipFile(B/original) as z:base=E.fromstring(z.read('word/document.xml'))
 # Compare logical text, math and image references without namespace serialization.
 sig=lambda root:[(text(p),[''.join(x.itertext()) for x in p.xpath('.//*[local-name()="oMath"]')],p.xpath('.//*[local-name()="blip"]/@*[local-name()="embed"]')) for p in root.xpath('//w:body//w:p',namespaces=N)]
 ck(name+' Reject All restores original logical content',sig(resolve(raw,False))==sig(base))
 bm=[''.join(x.itertext()) for x in base.xpath('//*[local-name()="oMath"]')]
 am=[''.join(x.itertext()) for x in (accepted if name=='Main' else raw).xpath('//*[local-name()="oMath"]')]
 ck(name+(' original accepted editable equations preserved' if name=='Main' else ' original math preserved in tracked/rejection content'),bm==am)
 ids=raw.xpath('//w:ins/@w:id|//w:del/@w:id|//w:pPrChange/@w:id',namespaces=N);ck(name+' unique revision IDs',len(ids)==len(set(ids)))

bud=readcsv(S/'downstream_metric_framework/exact_mse_budgets_with_external.csv');quality=readcsv(R/'auxiliary/quality/results/full_mse_decompositions.csv');cloud=readcsv(R/'auxiliary/native/cloud8/results/native_cloud_sensitivity.csv');point=readjson(O/'independent_claims_results.json')['results'];boot=readcsv(O/'independent_bootstrap_summary.csv')
ck('Point source audit PASS',readjson(O/'independent_claims_results.json')['status']=='PASS');ck('Bootstrap source audit PASS',readjson(O/'independent_bootstrap_results.json')['status']=='PASS')
def cell(table,row,col,expected,src):
 actual=table['rows'][row][col];ok=norm(actual)==norm(expected);ck(table['caption'].split('.')[0]+f' row{row}col{col}',ok,dict(actual=actual,expected=expected,source=str(src)));cells.append(dict(table=table['caption'].split('.')[0],row=row,col=col,actual=actual,expected=expected,passed=ok,source=str(src)))
Z=lambda x:f'{int(float(x)):,}';F=lambda x,n=4:f'{float(x):.{n}f}'

ck('SI exactly four tables',len(st)==4)
ck('SI captions numbered1to4',len(st)==4 and [re.match(r'Table S(\d+)\.',t['caption']).group(1) for t in st]==['1','2','3','4'])
ck('No remaining numbered Supplementary Notes',not re.search(r'Supplementary Notes?\s+S\d+',m+'\n'+s))
ck('No separately numbered Supplementary Data references',not re.search(r'(?:Supplementary\s+)?Data\s+S\d+',m+'\n'+s))
refs=[]
for match in re.finditer(r'\bTables?\s+S(\d+)(?:\s*[–-]\s*S?(\d+))?',m):refs.extend(range(int(match[1]),int(match[2] or match[1])+1))
ck('All main SI table references within1to4',bool(refs) and set(refs)<=set(range(1,5)),refs)
modern=[]
if len(st)==4:
 # Exact budgets: labels determine scientific cohort, not authoring row order.
 ck('S1ten data rows',len(st[0]['rows'])==11)
 for ri,row in enumerate(st[0]['rows'][1:],1):
  label=row[0];scope='transition' if 'transition' in label.lower() else 'hourly'
  sample='2021 external GOES17/16' if label.startswith('2021') else '2026 combined GOES18/19' if label.startswith('2026') else '2022-2024 expansion GOES18/16' if label.startswith('2022') else '2025 original GOES18/19' if 'original' in label else '2025 expansion GOES18/19'
  v=next(x for x in bud if x['sample']==sample and x['scope']==scope)
  vals=[Z(v['n'])]+[F(v[k]) for k in ['component_variance_gain_k2','differential_bias_gain_k2','covariance_loss_penalty_k2','net_downstream_mse_gain_k2']]
  for ci,val in enumerate(vals,1):cell(st[0],ri,ci,val,'exact_mse_budgets_with_external.csv')
 # Quality/cloud compact table. Reconstruct screen identifiers from readable labels.
 for ri,row in enumerate(st[1]['rows'][1:],1):
  label=norm(row[0]).lower();unit=row[1].lower()
  if unit in ['hourly','transition']:
   scenario='strict_common_daily' if 'dqf 0' in label else 'recommended_common_daily';v=next(x for x in quality if x['scenario']==scenario and x['level']==unit)
   vals=[Z(v['n'])+' / '+Z(v['cities']),F(v['raw_contrast_rmse_K'])+' / '+F(v['corrected_contrast_rmse_K']),F(v['net_contrast_mse_gain_K2'])]
  else:
   screen='recommended' if 'recommended' in label else 'ACM_clear_buffer2' if '2 pixel' in label else 'ACM_clear_buffer1' if '1 pixel' in label else 'ACM_clear'
   support='matched_to_ACM_clear_buffer2' if 'common' in label else 'native_screen_eligible';v=next(x for x in cloud if x['screen']==screen and x['support']==support)
   vals=[Z(v['n'])+' / '+Z(v['cities']),F(v['contrast_rmse_raw'])+' / '+F(v['contrast_rmse_corrected']),F(v['net_contrast_MSE_gain'])]
  for ci,val in enumerate(vals,2):cell(st[1],ri,ci,val,'quality/cloud per-observation summaries independently recomputed')
 ck('S2unfavorable strict transition retained',any('DQF 0' in row[0] and row[1]=='transition' and norm(row[3])=='0.8160 / 0.8399' for row in st[1]['rows'][1:]))
 # Directional count/fraction/criterion values independently calculated from raw
 # selected transitions and radius reconstructed from2025OOF residuals.
 ck('S3three cohort rows',len(st[2]['rows'])==4)
 for ri,row in enumerate(st[2]['rows'][1:],1):
  label=row[0].lower();v=next(x for x in point['directional'] if x['cohort']==label)
  vals=[Z(v['n']),f"{v['covered_n']}/{v['n']}; {100*v['coverage']:.1f}%",f"{v['supported_n']}/{v['n']}; {100*v['support_fraction']:.1f}%",f"{v['matching_supported_n']}/{v['supported_n']}; {100*v['agreement']:.1f}%",('Pass' if v['coverage_in_band'] else 'Fail')+' / '+('Pass' if v['agreement_at_least90'] else 'Fail')]
  for ci,val in enumerate(vals,1):cell(st[2],ri,ci,val,'independent selected-transition reconstruction')
 # Raw station metrics: CSV expected values independently reconstructed from
 # station/time rows; modern tier must be labeled separately in caption/main.
 hist=readcsv(R/'auxiliary/surface/results/full_metrics.csv');modernpath=O/'independent_modern_station_metrics.csv';modern=readcsv(modernpath) if modernpath.exists() else []
 sites={'Desert Rock':'dra','Fort Peck':'fpk','Table Mountain':'tbl','Pooled':'all'}
 for ri,row in enumerate(st[3]['rows'][1:],1):
  period=row[0];site=sites[row[1]];years=re.findall(r'20\d{2}',period);year=years[0] if len(years)==1 else 'all'
  if year=='2021':
   dim='pooled' if site=='all' else 'station';a=next(x for x in hist if x['dimension']==dim and x['group']==site and x['bucket']=='noaa-goes16');b=next(x for x in hist if x['dimension']==dim and x['group']==site and x['bucket']=='noaa-goes17');brmse='rmse'
  else:
   a=next(x for x in modern if str(x['year'])==year and x['site']==site and x['bucket']=='noaa-goes18');b=next(x for x in modern if str(x['year'])==year and x['site']==site and x['bucket']=='noaa-goes19');brmse='RMSE'
  vals=[Z(a['n']),F(a['bias'],3)+' / '+F(b['bias'],3),F(a[brmse],3)+' / '+F(b[brmse],3)]
  for ci,val in enumerate(vals,2):cell(st[3],ri,ci,val,'independently reconstructed raw station/time metrics')

# Main tables and material new/retained claims.
table1=next(x for x in mt if x['rows'][0][0]=='Stage');counts=readcsv(R/'pipeline/repaired/si_tables/cohort_attrition_summary.csv')
ids=['external_calibration_combined_2019_2020','external_validation_combined_2021','initial_model_derivation_original_2022_2024','initial_model_evaluation_expansion_2022_2024','initial_model_evaluation_original_2025','initial_model_evaluation_expansion_2025','metric_aware_validation_combined_2026']
for ri,sid in enumerate(ids,1):
 v=next(x for x in counts if x['stage_id']==sid)
 for ci,key in enumerate(['analyzed_cities','fixed_intervals','hourly_city_event_rows','eligible_transition_city_events'],3):cell(table1,ri,ci,Z(v[key]) if v[key] else '—','corrected cohort_attrition_summary.csv')
def has(label,parts,context=None):
 txt=context if context is not None else m
 for part in parts:ck(label+': '+part,part.lower() in txt.lower())
has('Posthoc temporal scope',['same 75 cities','post hoc corrected temporal evaluation','unseen cities remains untested'])
abstract=next(x for x in mp if x.startswith('Cross-platform harmonization targets'))
ck('Abstract explicit posthoc qualification','post hoc' in abstract.lower())
has('Fixed radius interpolation',['higher','1.5043'])
has('Primary paired quality support',['three','215','21 transitions','Tucson','South Valley','Albuquerque'])
has('Sparse strict screening boundary',['geography','view','three','75 cities'])
has('Cloud sampled support',['first local day','eight','scan-level'])
has('Ground QC and timing',['QC = 0','12 valid','15-minute','30 s'])
has('Historical covariance',[F(point['point_estimates']['2021 hourly']['raw_correlation'],3),F(point['point_estimates']['2021 hourly']['corrected_correlation'],3),'0.2085','1.2282','0.0064'])
has('LHP limit',['does not isolate LHP effects'])
has('Inputs not causally isolated',['emissivity','atmospheric','unresolved'])
has('Raw benchmark urban validation incomplete',['full urban','ground validation'])
has('Directional fractions distinct',['31.9%','94.6%','97.4%','79.0%','88.4%'])
has('Original and expansion negatives',['above','coverage','expansion'])
has('Scale ratios',['1.670','1.818','38.2%','44.2%','aggregate'])
has('2026 contrast uncertain',['−0.14%','−6.75%','+6.48%'])
if modern:
 has('Modern sample and year support',['282','173','109','2025','2026'])
 has('Modern quality restriction',['DQF','zero','strict','2021'])
 has('Modern station RMSE',[F(x['RMSE'],3) for x in modern if x['site']=='all' and str(x['year']) in ['2025','2026']])
 has('Ground scenarios differ from retrieval inputs',['ground','emissivity','ABI'])
ck('No stale prospective labels in accepted main',not re.search(r'\bprospective\b',m,re.I))
ck('No old numerical supports',all(x not in m+'\n'+s for x in ['5,744','2,571','1.535818','0.9929','1.0302']))

figs=[B/'integration_20261029/figures/Figure_1_corrected_workflow_domain_chronology.png',R/'figures/Figure_2_repaired_model_selection.png',R/'figures/Figure_3_repaired_cross_platform_budget.png',R/'figures/Figure_4_repaired_covariance_regimes.png',R/'figures/Figure_5_repaired_replication_and_temporal_evaluation.png',R/'figures/Phoenix_LST_corrected_local_date.png']
ck('Exactly six accepted figures',len(images)==6)
for i,p in enumerate(figs):ck(f'Figure{i+1}source bytes match',len(images)>i and images[i]==sha(p))
eq=[]
for p in mp:
 if re.fullmatch(r'[,\s]*\(\d+\)',p):eq.extend(int(x) for x in re.findall(r'\((\d+)\)',p))
ck('12equations in sequence',eq==list(range(1,13)),eq)
refstart=next(i for i,p in enumerate(mp) if p=='References');refs=[x for x in mp[refstart+1:] if x.strip() and not x.startswith('Disclaimer/')];ck('34references',len(refs)==34,len(refs));dois=[d for ref in refs for d in re.findall(r'https://doi\.org/\S+',ref)];ck('No duplicate DOI',len(dois)==len(set(dois)))
ck('Independent audited inputs unchanged',all(sha(Path(p))==h for p,h in readjson(O/'independent_claims_results.json')['input_hashes'].items()))
(O/'final_word_cell_comparisons.json').write_text(json.dumps(cells,indent=2,ensure_ascii=False));out=dict(status='PASS' if all(x['passed'] for x in checks) else 'FAIL',documents={k:{x:v[x] for x in ['path','sha256']} for k,v in documents.items()},checks=checks,compared_cells=len(cells),source_hashes=sources,limitations=['This audit verifies content/structure and source consistency; visual rendering is separately required.','No response-letter cross-check is claimed; letters are deferred by the user.'])
(O/'final_word_audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False));print(json.dumps(dict(status=out['status'],checks=len(checks),compared_cells=len(cells),failed=[x for x in checks if not x['passed']]),indent=2))
if out['status']!='PASS':raise SystemExit(1)
