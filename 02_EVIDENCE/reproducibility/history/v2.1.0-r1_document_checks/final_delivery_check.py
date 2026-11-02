"""Small read-only final delivery check of the final Word bytes and citations."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json,re,hashlib,datetime
B=Path('/Users/apple/Downloads/RS revision 1');C=B/'continuation_20261029';O=C/'science/claims_audit';N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};q=lambda x:'{'+N['w']+'}'+x;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def ck(name,ok,details=None):checks.append(dict(check=name,passed=bool(ok),details=details))
def current(name):
 p=B/name
 with ZipFile(p) as z:
  r=E.fromstring(z.read('word/document.xml'));comments=E.fromstring(z.read('word/comments.xml'))
  ct=[dict(id=c.get(q('id')),text=''.join(c.xpath('.//w:t/text()',namespaces=N))) for c in comments]
  for c in ct:
   for tag in ['commentRangeStart','commentRangeEnd','commentReference']:ck(name+' comment '+tag,len(r.xpath('//w:'+tag+'[@w:id="'+c['id']+'"]',namespaces=N))==1)
  for x in list(r.xpath('//w:tr[w:trPr/w:del]|//w:p[w:pPr/w:rPr/w:del]',namespaces=N)):
   if x.getparent() is not None:x.getparent().remove(x)
  for x in list(r.xpath('//w:del',namespaces=N)):
   if x.getparent() is not None:x.getparent().remove(x)
  for x in reversed(r.xpath('//w:ins',namespaces=N)):
   par=x.getparent()
   if par is None:continue
   i=par.index(x)
   for child in list(x):x.remove(child);par.insert(i,child);i+=1
   par.remove(x)
  text=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=N))
  ps=[text(p) for p in r.xpath('//w:body//w:p',namespaces=N)];tables=[t for t in r.xpath('//w:body/w:tbl',namespaces=N) if t.findall(q('tr'))]
  return p,r,ps,tables,ct
m,mr,mp,mt,mc=current('Manuscript v1_suggestions.docx');s,sr,sp,st,sc=current('supplementary_suggestions.docx');M='\n'.join(mp);S='\n'.join(sp)
old=json.loads((O/'final_word_audit.json').read_text());ck('Scientific Word audit PASS',old['status']=='PASS',dict(checks=len(old['checks']),cells=old['compared_cells']))
for p,key in [(m,'manuscript'),(s,'si')]:
 ck(p.name+' matches independently audited bytes',sha(p)==old['documents'][p.name]['sha256'],sha(p))
 ps=mp if key=='manuscript' else sp
 recorded=(C/f'records/{key}_final_accepted.txt').read_text();ck(key+' final accepted text matches current Word','\n'.join(ps).strip()==recorded.strip())

body=mp[:mp.index('References')];seen=[]
for p in body:
 for token in re.findall(r'\[([\d,\s–-]+)\]',p):
  for part in token.split(','):
   part=part.strip();match=re.fullmatch(r'(\d+)\s*[–-]\s*(\d+)',part)
   nums=list(range(int(match[1]),int(match[2])+1)) if match else [int(part)]
   for n in nums:
    if n not in seen:seen.append(n)
ck('Main citation first appearance exactly1to34',seen==list(range(1,35)),seen)
ref=mp[mp.index('References')+1:];ref=[p for p in ref if p.strip() and not p.startswith('Disclaimer/')];ck('34numbered reference entries',len(ref)==34)
ck('Exactly four accepted SI tables',len(st)==4,len(st));captions=[p for p in sp if re.match(r'Table S\d+\.',p)];ck('SI caption sequence S1toS4',[int(re.match(r'Table S(\d+)\.',p)[1]) for p in captions]==[1,2,3,4])
ck('SI data rows10/9/3/12',[len(t.findall(q('tr')))-1 for t in st]==[10,9,3,12])
si_refs=[]
for match in re.finditer(r'\bTables?\s+S(\d+)(?:\s*[–-]\s*S?(\d+))?',M):si_refs.extend(range(int(match[1]),int(match[2] or match[1])+1))
ck('All SI tables referenced and no out-of-range references',set(si_refs)=={1,2,3,4},si_refs)
ck('No old numbered Notes or Data references',not re.search(r'(?:Supplementary Notes?|(?:Supplementary\s+)?Data)\s+S\d+',M+'\n'+S))
ck('One remaining publication comment only',len(mc)==1 and not sc and 'Release authorization pending' in mc[0]['text'],mc)
ck('No new inaccessible releaseURL or DOI claimed','public release is pending' in M and '/releases/tag/v2.1.0-r1' not in M and '/releases/download/v2.1.0-r1' not in M)
clauses={
 'Modern strict0no common pair':'A strict-DQF-0 feasibility check yielded no common GOES-18/19 pair',
 'All modern paired G19mediumquality':'All 282 retained GOES-19 pixels were DQF 1',
 'Different eras not ranked':'preclude a direct cross-era skill comparison',
 'Modern first-day rather than full period':'first local day of each of the ten 2025 and eight 2026 study intervals',
 'No urbantrained station corrections':'City-trained corrections are not applied to station pixels',
 'Urban fullchain groundvalidation still incomplete':'full urban-workflow ground validation remains open',
 'LHPcalendar doesnotisolatecause':'does not isolate LHP effects',
 'Ground scenarios not ABI input perturbations':'These scenarios do not perturb actual ABI retrieval inputs',
 'Same75cities':'same 75 cities as the 2025 calibration',
 'Posthoc corrected temporal scope':'post hoc corrected temporal evaluation of the original protocol',
 'Final unseen-city performance untested':'Spatial generalization of the final 2025-selected workflow to unseen cities remains untested',
 'Expansionbothfail':'below both criteria',
 'Originalovercoverage':'original-cohort coverage was 97.4%, above the 85–95% band',
 'Conditional31.9support94.6agreement':'excluded zero in 186 cases (31.9%)',
 'Uncertain2026contrast':'contrast RMSE reduction was −0.14%',
 'Higher empirical quantile':'using the higher empirical quantile',
 'Sparse strictgeography':'These three cities are geographically clustered',
 'Conditional strictpopulation':'cannot establish robustness across all 75 cities',
 'Yearly methods seed distinction':'Primary model-fitting and crossed city–interval resampling used the fixed integer random seed 20260810',
 'Modern station bootstrapseed':'seed 20261029 for the modern benchmark',
}
for name,clause in clauses.items():ck(name,clause in M)
ck('No prospective label in current body',not re.search(r'\bprospective\b',M,re.I))
out=dict(status='PASS' if all(c['passed'] for c in checks) else 'FAIL',date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),documents={str(p):sha(p) for p in [m,s]},checks=checks,limitations=['No final response-letter cross-check: reviewer response letters are deliberately deferred.','Public release still requires explicit authorization and actual accessible publication.','Visual QA is separately recorded by the coordinator; this is a content/citation/byte-binding audit.'])
(O/'final_delivery_independent_check.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
summary=f'''# Final independent delivery check

30 October 2026. Status: **{out['status']}**; {sum(c['passed'] for c in checks)}/{len(checks)} checks pass.

The current Word bytes match the final independent scientific audit (256 checks, 156 numeric/boolean table-cell comparisons). Current accepted text also matches the coordinator's final manuscript/SI text files. Main reference first-appearance order is exactly1–34. The compact SI has four numbered tables, with10/9/3/12 data rows, all referenced and no dangling numbered Note/Data references.

One anchored comment remains, concerning approval/publication of the prepared release. No release-specific inaccessible URL or invented DOI has been asserted. Both files retain Track Changes; accepting changes is still the author's action.

The final text explicitly preserves all282modernGOES-19pixels being DQF1, zerojointstrict0support, the first-local-day sample, differing historical/modern quality policies, no cross-era ranking, and incomplete full urban ground validation. It also retains statistical-versus-causal covariance interpretation, June-only non-isolation of LHP, ground-versus-ABI-input sensitivity distinction, same75cities/posthoc temporal status, unseen-city limitation, uncertain contrast change, original overcoverage and both expansion failures. The primary and modern station bootstrap seeds are now separately scoped.

No glaring new scientific claim error was identified in this final read-only pass. Detailed assertions and current Word SHA256s are in the companion JSON. This is not a submission-readiness declaration: the user has deferred response letters, their final line/claim cross-check cannot yet be complete, and public release still needs authorization. Visual QA is separately recorded by the coordinator.
'''
(O/'final_delivery_independent_check.md').write_text(summary)
print(json.dumps(dict(status=out['status'],checks=len(checks),failed=[c for c in checks if not c['passed']]),indent=2))
if out['status']!='PASS':raise SystemExit(1)
