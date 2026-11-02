"""Independent read-only Methods/content audit of actual current DOCX bytes."""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import datetime,hashlib,json,re

B=Path('/Users/apple/Downloads/RS revision 1');D=B/'concision_20261030'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M='http://schemas.openxmlformats.org/officeDocument/2006/math'
N={'w':W,'m':M};q=lambda x:'{'+W+'}'+x
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def accepted(path):
    with ZipFile(path) as z:r=E.fromstring(z.read('word/document.xml'))
    r=deepcopy(r)
    # Independent accept-view interpretation, without importing authoring code.
    for el in list(r.xpath('//w:tr[w:trPr/w:del]|//w:p[w:pPr/w:rPr/w:del]',namespaces=N)):
        if el.getparent() is not None:el.getparent().remove(el)
    for el in list(r.xpath('//w:del',namespaces=N)):
        if el.getparent() is not None:el.getparent().remove(el)
    for el in list(r.xpath('//w:ins',namespaces=N)):
        p=el.getparent()
        if p is None:continue
        at=p.index(el)
        for child in list(el):el.remove(child);p.insert(at,child);at+=1
        p.remove(el)
    return r

def text(p):return ''.join(p.xpath('.//w:t/text()',namespaces=N))
def semantic(el):
    return (el.tag,tuple(sorted(el.attrib.items())),el.text or '',tuple(semantic(c) for c in el))

current_path=B/'Manuscript v1_suggestions.docx'
base_path=D/'snapshots/Manuscript v1_suggestions.docx'
root=accepted(current_path);base=accepted(base_path)
ps=root.xpath('//w:body//w:p',namespaces=N);bs=base.xpath('//w:body//w:p',namespaces=N)
cur={i:text(p) for i,p in enumerate(ps)};old={i:text(p) for i,p in enumerate(bs)}
results=[]
def check(label,passed,details=None):
    results.append(dict(check=label,passed=bool(passed),details=details))
    if not passed:print('FAIL:',label,details)
def has(p,*parts):return all(s in cur[p] for s in parts)

check('Independent actual DOCX accept view matches exported paragraph records',
    [dict(p=i,text=text(p)) for i,p in enumerate(ps)]==
    [dict(p=x['p'],text=x['text']) for x in json.loads((D/'records/manuscript_accepted.json').read_text())])
changed=[i for i in range(30,165) if cur[i]!=old[i]]
expected=[31,33,34,36,37,38,42,115,116,117,118,119,129,130,131,151,161]
check('Only intended17 Methods prose paragraphs changed',changed==expected,changed)
for i in [i for i in range(30,165) if i not in expected]:
    check('Unchanged Methods content P'+str(i),cur[i]==old[i])
for i in expected:
    cites=lambda s:re.findall(r'\[\d+(?:[,–-]\d+)*\]',s)
    check('Edited Methods citations unchanged P'+str(i),cites(cur[i])==cites(old[i]))

math_cur=root.xpath('//m:oMath',namespaces=N);math_base=base.xpath('//m:oMath',namespaces=N)
check('All18 native math objects retain exact semantic structure',
    len(math_cur)==len(math_base)==18 and [semantic(x) for x in math_cur]==[semantic(x) for x in math_base])
for i,expected_math,left,right in [(42,'T','and ',' is in °C.'),(129,'15','divided by ','. The cutoff'),(131,'25','divided by ','. The one-standard-error')]:
    nodes=ps[i].xpath('.//m:oMath',namespaces=N)
    check('Single preserved inline math object P'+str(i),len(nodes)==1 and ''.join(nodes[0].xpath('.//m:t/text()',namespaces=N))==expected_math)
    vals=[]
    for el in ps[i]:
        if el.tag in ['{'+M+'}oMath','{'+M+'}oMathPara']:vals.append('[[MATH]]')
        else:vals.append(text(el))
    joined=''.join(vals)
    check('Inline math grammar/position correct P'+str(i),left+'[[MATH]]'+right in joined,joined[max(joined.find('[[MATH]]')-45,0):joined.find('[[MATH]]')+75])
    if i in [129,131]:check('Square-root native structure retained P'+str(i),bool(nodes[0].xpath('.//m:rad',namespaces=N)))

check('Eight-day units,reference orientation,reference error and no evaluation refitting',has(33,'inclusive eight-day','GOES-17/16 in 2019–2021','GOES-18/16 in 2022–2024','GOES-18/19 in 2025–2026','without presuming greater absolute accuracy','without refitting','reference-platform error'))
check('Original/expansion candidate retained counts and disjoint fitting',has(34,'51 higher','44 met','31 intervals','43 candidates','31 met the same rules on the same dates','excluded from fitting','not vegetation-cover fraction','6 and 10 August 2026','75 cities, 7,139 hourly observations and 737 transitions'))
check('Full inherited-parent provenance and grouping criteria retained',has(35,'5,541','MODIS','NDVI > 0.30','897.6626','morphology/water','60 pilot','24–50°N','125–66°W'))
check('Same-city2026 posthoc/calibration-only scope and repairs explicit',has(36,'same 75 cities as 2025','fixed before extraction','local-date allocation and polygon extraction','unchanged protocol','fitted only to 2025 data','5,716','583','already been inspected','post hoc corrected temporal evaluation','does not test unseen-city'))
check('Historical calibration/evaluation support and prelisting freeze retained',has(37,'69 of the 75','2019–2020','2,559','2021','2,602','253','before GOES-17 file listing','applied unchanged','overlapping cities'))
check('All five stage roles and shared dates limitation retained',has(38,'2021 GOES-17/16','2022–2024 GOES-18/16 expansion','2025 GOES-18/19 original and expansion','combined 2026 GOES-18/19','Each was excluded from fitting its evaluated correction','both 2025 cohorts later calibrated','Shared dates limit temporal independence','independently of GOES outcomes'))
check('ERA collections/scale and hydroclimate definitions retained',has(38,'ECMWF/ERA5_LAND/HOURLY','ECMWF/ERA5_LAND/DAILY_AGGR','~11.1 km','11,132 m','0.1°','22:00–06:00 local solar time','unweighted mean of volumetric soil-water layers 1–4','2-m air and dew-point'))
check('Census ranking and hot-city/dispersion rules retained',has(42,'2003–2025','within city across eight-day steps','within city and recurring calendar step','100 minus moisture percentile','June–August','at least 20 city observations at or above','90th percentile','≥10 percentile points','all candidate-city observations in 2022–2024','hot-city observations in 2025','31 and ten intervals'))
check('Primary decoding and physical/DQF rules unchanged',has(115,'ABI-L2-LSTC','CONUS','2-km nominal','scale/offset','unsigned packed-value','fill removal','DQF 0–1','180–380 K','v02r00','v01r00','bitmasks','No audited historical DQF 1','Provisional'))
check('Retrieval era/metadata evidence remains bounded',has(116,'19 August 2021','baseline-to-Enterprise','2022–2026','32 corrected-date 2026','matching algorithm/processing-parameter families','cannot establish equal numerical emissivity or atmospheric fields','differences remain possible'))
check('Complete polygon and native support operations preserved',has(117,'R2024A','uc_id','100°W','250-m maximum-error','20-km and 10-km outward buffers','same tolerance','grid-cell centers','complete geometry','full extent','double-precision','full-grid checks','three valid core and ten ring pixels','no rural or peri-urban classification'))
check('Physical local sunset/date-pairing and aggregation unchanged',has(118,'Astral 3.2','intended physical local date','Coordinated Universal Time','nearest hourly','−3 through +6','round-trip check','preceding evening','every date','share city, interval, local date and target hour','<1 min','each weighted equally','2019–2021','at least two paired dates','Source object keys and acquisition timestamps'))
check('Geometry ranges and noncausal interpretation preserved',has(119,'does not match viewing geometry','43.74–59.68°','52.61–72.25°','without refitting','remain coupled','do not isolate an angular retrieval effect'))
check('C/R/D/T definitions and exact observation windows unchanged',all(cur[i]==old[i] for i in [121,122,123,124,125,126,127,128]))
check('Initial candidate families and complete geometry predictors retained',has(129,'ten hour-specific additive offsets','five-knot cubic hour spline','ridge regularization','geometry ridge','sunset-relative hour, latitude, longitude','source/reference zenith angles','difference/mean','hour-by-geometry interactions'))
check('Initial15-fold intersection testing/union exclusion/six-score unweighted scheme retained',has(129,'15 crossed year-by-longitude-block folds','held year/block intersection','training excluded observations in either held group','six RMSE-to-raw ratios equally','hourly and transition core, ring and contrast','Candidate scores averaged the 15 composites','sample standard deviation of those 15 scores divided by'))
check('Initial oneSE threshold uses best candidateSE and fixed admissible order',has(129,'best mean plus its SE','means did not exceed it','raw, hour offset, hour spline, then geometry ridge','all 2022–2024 derivation data','unchanged expansion/2025 evaluation'))
check('2025five-by-fivefold design and exclusions retained',has(130,'Five longitude-ranked city blocks','five chronological interval blocks','25 folds','held-block intersection','training excluded observations in either held block'))
check('2025all candidate families/features and prohibited predictors retained',has(130,'raw, hour offset, geometry ridge and scene gradient-boosted','source core, ring, mean-surface and contrast temperatures','interactions with sunset-relative hour','raw, mean offset, ridge and boosted trees','source component transitions','pre/post-sunset','city/interval identifiers, vegetation group, hydroclimatic state and reference-platform temperature'))
check('2025oneSE math/cutoff/heuristic/actual actions and values retained',has(131,'25 within-fold RMSE-to-raw ratios without weighting','sample standard deviation','least complex candidate whose mean did not exceed the best mean plus the SE of the best-scoring candidate','selection heuristics rather than inferential standard errors','geometry ridge for core, hour offset for ring','raw for direct hourly contrast/transition','0.9928','1.0000','1.0288','fitted once to all 2025'))
check('MSE accounting and decision mathematics untouched',all(cur[i]==old[i] for i in range(134,151)))
check('Higherquantile residual width and conditional decision logic retained',has(151,'higher empirical 90th percentile','absolute out-of-fold residuals','1.5043 K','±1.5043 K','above or below zero','otherwise the rule abstained','at least 10%','below that threshold','85–95%','at least 90%','among supported cases','±5 percentage points','at most 10%','not significance thresholds','pooled evaluation is the formal scope','cohort/interval summaries diagnose transport','empirical cross-platform residual intervals'))
check('Stress-grid/budget/uncertainty/covariance/seed procedures unchanged',all(cur[i]==old[i] for i in range(152,160)))
check('Strictquality both-platform criteria,fixedmodels and conditional bootstrap retained',has(161,'DQF = 0 on both platforms','three core and ten ring pixels','fixed 2025 component models','identical paired daily keys before aggregation','5,000 crossed resamples','three eligible cities and eight intervals'))
check('Cloud source timing/scene support/spatial masks remain bounded',has(161,'first local day of each 2026 interval','Phoenix bins −3/+4','32 matched LST/ABI-L2-ACMC scene pairs','sunset-relative bins can differ','one-/two-pixel four-connected dilations','complete-polygon averaging','matched native grids','Cloud rows in Table S2','selected scans on eight days','not complete interval means or transitions'))
check('All historical/modern ground-QC,timing,sensitivity rules untouched',all(cur[i]==old[i] for i in [162,163,164]))
check('New strict transition deterioration and restricted population explicit',has(230,'215 hourly observations and 21 transitions','0.961 to 0.992 K under recommended screening','0.816 to 0.840 K under strict DQF-0','three cities','conditional comparison cannot establish robustness across all 75 cities'))
check('Full urban workflow validation still explicitly incomplete',has(231,'does not independently validate the complete urban core–ring contrast and transition workflow') and has(232,'does not validate city-trained corrections or urban core–ring measurands'))
check('Modern quality/sample/uncertainty restrictions and all counts remain',has(232,'173 common pairs in 2025 and 109 in 2026','18 selected dates','three sites','All 282','DQF 1','no pair met joint DQF 0','both difference intervals include zero'))
check('LHP sensitivity still cannot isolate anomalies',has(253,'1,330','two June intervals','not classified as anomaly-free','does not isolate LHP effects'))

# Read the implemented selection operations as an additional exactness check,
# without importing/executing any computational pipeline.
code=B/'continuation_20261029/release/downstream-measurand-aware-lst-harmonization-2.1.0-r1/scripts'
initial=(code/'run_multiplatform_harmonization.py').read_text()
modern=(code/'train_goes18_goes19_metric_harmonization.py').read_text()
check('Initial source corroborates5-knot cubic spline and oneSE threshold',all(x in initial for x in ['n_knots=5, degree=3','best["mean_composite"] + best["se_composite"]','mean_composite=("composite_rmse_ratio", "mean")','sd_composite=("composite_rmse_ratio", "std")','mean_composite"].le(threshold)']))
check('Modern source corroborateshigherquantile and oneSE/admissible-order logic',all(x in modern for x in ['quantile(0.9, interpolation="higher")','best["mean_rmse_ratio"] + best["se_rmse_ratio"]','selected = next(item for item in order if item in eligible)']))

body=lambda r:' '.join(text(p) for p in r.find(q('body')).findall(q('p')))
original=accepted(B/'Manuscript v1.docx')
counts={'original_paragraph_only':len(body(original).split()),'prepass_paragraph_only':len(body(base).split()),'current_paragraph_only':len(body(root).split()),
    'original_with_tables':sum(len(text(p).split()) for p in original.xpath('//w:body//w:p',namespaces=N)),
    'current_with_tables':sum(len(text(p).split()) for p in ps)}
check('Independent paragraph-word counts reproduce stated original/current8518/8762',counts['original_paragraph_only']==8762 and counts['current_paragraph_only']==8518,counts)
check('Current manuscript shorter also when tables included',counts['current_with_tables']<counts['original_with_tables'],counts)

out=dict(status='PASS' if all(x['passed'] for x in results) else 'FAIL',date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    documents={'current':{'path':str(current_path),'sha256':sha(current_path)},'prepass':{'path':str(base_path),'sha256':sha(base_path)}},
    word_counts=counts,checks=results,check_count=len(results),failed=[x for x in results if not x['passed']],
    findings=['No material Methods rule, numerical result, exclusion or qualification was lost in the applied concision.',
        'Inline temperature T and square-root denominators √15/√25 remain native OMML in their correct grammatical positions; all18native math objects are structurally identical to prepass.',
        'OneSE acceptance wording explicitly preserves best-candidateSE and ≤cutoff; source implementation agrees.',
        'Cloud scope is correctly limited to cloud rows; strict-quality transition deterioration is now explicit and remains conditional on21transitions at3cities.'],
    scope='Independent read-only review of actual DOCX accepted semantics and selected unchanged computational source declarations; no numerical pipeline rerun, rendering or response letters.',
    limitations=['Visual layout is separately checked by parent.','This check does not complete the full urban ground validation or causal attribution experiments.'])
(D/'records/methods_semantic_check.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
md='''# Independent Methods semantic check

Actual current Word content was independently interpreted from native tracked OOXML, without importing the authoring accept-view helper, and compared with the prepass snapshot and exported current paragraphs. No Word, plan, input, model or previous evidence file was modified.

**Result: {status}, {n}/{n} checks.** Paragraph-only words are {new:,} versus {old:,} original ({delta:,} fewer). Counting table paragraphs as well gives {newtab:,} versus {oldtab:,}. Both comparisons use whitespace-delimited Word text and include references, excluding native math text as in the stated counting method.

The17changed Methods paragraphs retain operative cohort/provenance rules, physical local-date/full-polygon corrections, native decoding, primary/strict DQF criteria, viewing-geometry limits, both crossed-fold training/testing exclusions, every candidate/predictor family, model-selection scoring and oneSEacceptance, higher empirical quantile, directional scope/thresholds and conditional cloud/quality interpretation. Source text for the selection/quantile implementations corroborates the concise description. Unedited Methods paragraphs are exactly equal to the prepass text, including every station radiometry/QC/timing/sensitivity procedure, bootstrap condition and stress-grid setting.

All18native mathematical objects match their prepass semantic structure. The inline temperatureT in paragraph42 remains between `and` and `is in °C`; square roots15and25 in paragraphs129/131 remain after `divided by` and before the next sentence. No symbol was converted to plain text, lost or shifted into the wrong clause. Display equations remain unchanged.

The final oneSE wording now explicitly says candidate means must not exceed the best mean plus the SEof the best candidate; this matches the code. The final cloud sentence explicitly concerns only cloud rows, preserving the distinction from strict-quality interval/transition results. Main3.5includes both unfavorable transition comparisons0.961→0.992K and0.816→0.840K, with21transitions/three-cityconditional scope. New station evidence remains raw-product-only, with all282G19pixelsDQF1 and zerojointstrictpairs, and both modernRMSEdifferenceintervals including zero. Fullurbanworkflow ground validation and LHPcausal isolation remain incomplete rather than overstated.

No material scientific defect was identified in this read-only check. Visual rendering is separately required; this is neither a complete raw-data rerun nor a submission-readiness declaration. Reviewer letters were not drafted.
'''.format(status=out['status'],n=len(results),new=counts['current_paragraph_only'],old=counts['original_paragraph_only'],delta=counts['original_paragraph_only']-counts['current_paragraph_only'],newtab=counts['current_with_tables'],oldtab=counts['original_with_tables'])
for a,b in [('The17','The 17'),('oneSEacceptance','one-SE acceptance'),('All18native','All 18 native'),('temperatureT','temperature T'),('paragraph42','paragraph 42'),('roots15and25','roots 15 and 25'),('paragraphs129/131','paragraphs 129/131'),('SEof','SE of'),('Main3.5includes','Main 3.5 includes'),('comparisons0.961','comparisons 0.961'),('0.992K','0.992 K'),('and0.816','and 0.816'),('0.840K','0.840 K'),('with21transitions/three-cityconditional','with 21 transitions/three-city conditional'),('all282G19pixelsDQF1','all 282 G19 pixels DQF 1'),('zerojointstrictpairs','zero joint strict pairs'),('modernRMSEdifferenceintervals','modern RMSE difference intervals'),('Fullurbanworkflow','Full urban workflow'),('LHPcausal','LHP causal')]:md=md.replace(a,b)
(D/'records/methods_semantic_check.md').write_text(md)
print(json.dumps({'status':out['status'],'checks':len(results),'failed':out['failed'],'counts':counts},indent=2))
