"""Independent structural/word-count/identity checks for concise Word outputs."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import hashlib,json,re,sys
B=Path('/Users/apple/Downloads/RS revision 1');D=B/'concision_20261030'
sys.path.insert(0,str(B/'continuation_20261029/scripts'))
from edit_documents import resolve
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W=N['w'];q=lambda x:'{'+W+'}'+x
schema=E.XMLSchema(E.parse('/Users/apple/.codex/skills/docx/scripts/office/schemas/ISO-IEC29500-4_2016/wml.xsd'))
allowed={W,'http://schemas.openxmlformats.org/officeDocument/2006/math','http://schemas.openxmlformats.org/drawingml/2006/main','http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','http://schemas.openxmlformats.org/drawingml/2006/picture'}
attrs=allowed|{'http://www.w3.org/XML/1998/namespace',N['r']}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
text=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=N))
def load(path):
    with ZipFile(path) as z:
        assert z.testzip() is None
        parts={n:z.read(n) for n in z.namelist()}
    return parts,E.fromstring(parts['word/document.xml'])
def sig(r):return [(text(p),[''.join(m.itertext()) for m in p.xpath('.//*[local-name()="oMath"]')],p.xpath('.//*[local-name()="blip"]/@*[local-name()="embed"]')) for p in r.xpath('//w:body//w:p',namespaces=N)]
def images(parts,r):
    rels={x.get('Id'):x.get('Target') for x in E.fromstring(parts['word/_rels/document.xml.rels'])}
    return [hashlib.sha256(parts['word/'+rels[x.get('{'+N['r']+'}embed')]]).hexdigest() for x in r.xpath('//a:blip',namespaces=N)]
def citeorder(ps):
    out=[]
    for p in ps:
        if text(p)=='References':break
        for m in re.finditer(r'\[(\d+(?:\s*[,–-]\s*\d+)*)\]',text(p)):
            for seg in m[1].split(','):
                a=re.split('[–-]',seg);nums=list(range(int(a[0]),int(a[-1])+1)) if len(a)==2 else [int(a[0])]
                for v in nums:
                    if v not in out:out.append(v)
    return out
checks=[]
def ck(label,yes,details=None):
    checks.append(dict(check=label,passed=bool(yes),details=details));assert yes,(label,details)
base=json.loads((D/'records/baseline.json').read_text());summaries=[]
for z in base:
    ck('Baseline snapshot immutable '+z['file'],sha(D/'snapshots'/z['file'])==z['sha256'])
    if 'suggestions' not in z['file']:ck('Original immutable '+z['file'],sha(B/z['file'])==z['sha256'])
for doc,name,orig in [('manuscript','Manuscript v1_suggestions.docx','Manuscript v1.docx'),('si','supplementary_suggestions.docx','supplementary.docx')]:
    parts,raw=load(B/name);bp,original=load(B/orig);pp,prior=load(D/'snapshots'/name)
    acc=resolve(raw,True);rej=resolve(raw,False);pacc=resolve(prior,True)
    ck(doc+' RejectAll restores original logical content',sig(rej)==sig(original))
    math=lambda r:[''.join(x.itertext()) for x in r.xpath('//*[local-name()="oMath"]')]
    ck(doc+' original editable math preserved',math(original)==math(acc if doc=='manuscript' else rej))
    ck(doc+' complete media unchanged',all(parts[n]==v for n,v in pp.items() if n.startswith('word/media/')))
    ck(doc+' tracking enabled',E.fromstring(parts['word/settings.xml']).find(q('trackRevisions')) is not None)
    ids=raw.xpath('//w:ins/@w:id|//w:del/@w:id|//w:pPrChange/@w:id',namespaces=N)
    ck(doc+' unique revision IDs',len(ids)==len(set(ids)))
    ck(doc+' deletion text properly encoded',not raw.xpath('//w:del//w:t',namespaces=N))
    cs=E.fromstring(parts['word/comments.xml']);ck(doc+' comment count',len(cs)==(1 if doc=='manuscript' else 0))
    for c in cs:
        cid=c.get(q('id'))
        for tag in ['commentRangeStart','commentRangeEnd','commentReference']:
            ck(doc+' author comment anchor '+tag,len(raw.xpath('//w:'+tag+'[@w:id="'+cid+'"]',namespaces=N))==1)
    for member in ['word/document.xml','word/settings.xml','word/comments.xml']:
        x=E.fromstring(parts[member])
        for e in list(x.iter()):
            if not isinstance(e.tag,str):continue
            if E.QName(e).namespace not in allowed and e.getparent() is not None:e.getparent().remove(e);continue
            for k in list(e.attrib):
                if k.startswith('{') and E.QName(k).namespace not in attrs:del e.attrib[k]
        ck(doc+' OOXML schema '+member,schema.validate(x),[e.message for e in schema.error_log])
    ps=acc.xpath('//w:body//w:p',namespaces=N);txt='\n'.join(map(text,ps))
    ck(doc+' no old SI notes/data references',not re.search(r'Supplementary Notes?\s+S\d|Supplementary Data S\d',txt))
    ck(doc+' no nonexistent SI tables',not re.search(r'Tables? S(?:[6-9]|\d{2})\b',txt))
    if doc=='manuscript':
        direct=acc.xpath('//w:body/w:p',namespaces=N)
        counts=dict(paragraph_words=sum(len(text(p).split()) for p in direct),table_inclusive_words=sum(len(text(p).split()) for p in ps))
        ck('Manuscript shorter than original by requested method',counts['paragraph_words']<8762,counts)
        ck('Manuscript also shorter including table cells',counts['table_inclusive_words']<9105,counts)
        ck('Six current figure identities preserved',images(parts,acc)==images(pp,pacc) and len(images(parts,acc))==6)
        equations=[int(v) for p in ps if re.fullmatch(r'[,\s]*\(\d+\)',text(p)) for v in re.findall(r'\((\d+)\)',text(p))]
        ck('12 equations in sequence',equations==list(range(1,13)),equations)
        ck('Reference first appearance order1to34',citeorder(ps)==list(range(1,35)),citeorder(ps))
        refs=lambda r:[text(p) for p in r.xpath('//w:p[w:pPr/w:pStyle[@w:val="MDPI81references"]]',namespaces=N)]
        ck('34 bibliographic identities unchanged',refs(acc)==refs(pacc) and len(refs(acc))==34)
        ck('Exact strict transition results explicit in main',all(v in txt for v in ['0.961','0.992','0.816','0.840','21 transitions','three cities']))
        ck('Key negative findings retained',all(v in txt for v in ['−0.14%','−6.75%','+6.48%','31.9%','94.6%','97.4%','79.0%','88.4%']))
        ck('Principal covariance values retained',all(v in txt for v in ['0.2085','1.2282','0.0064']))
        ck('Principal station numbers retained',all(v in txt for v in ['413','173','109','282','1.904','2.573','2.137','2.351']))
        ck('S5 referenced in main','Table S5' in txt)
    else:
        tables=acc.xpath('//w:body/w:tbl',namespaces=N);ck('Five compact SI tables',len(tables)==5)
        caps=[text(p) for p in acc.xpath('//w:body/w:p',namespaces=N) if re.match('Table S[1-5]\\.',text(p))]
        ck('SI captions1to5',len(caps)==5 and [c[7] for c in caps]==list('12345'))
        prior_tables=pacc.xpath('//w:body/w:tbl',namespaces=N)
        # Inspect each table subtree rather than the document-level body XPath.
        cells=lambda t:[text(p) for p in t.xpath('.//w:p',namespaces=N)]
        ck('All prior SI cell values preserved',[cells(t) for t in tables[:4]]==[cells(t) for t in prior_tables])
        spec=json.loads((D/'plans/si_addition.json').read_text())['table']
        actual=[[' '.join(text(p) for p in tc.findall(q('p'))) for tc in tr.findall(q('tc'))] for tr in tables[4].findall(q('tr'))]
        ck('S5 all source-verified cells match',actual==[spec['headers']]+spec['rows'])
        counts=dict(paragraph_words=sum(len(text(p).split()) for p in acc.xpath('//w:body/w:p',namespaces=N)),table_inclusive_words=sum(len(text(p).split()) for p in ps))
    summaries.append(dict(doc=doc,status='PASS',sha256=sha(B/name),revisions=len(ids),counts=counts))
out=dict(status='PASS',checks=checks,documents=summaries)
(D/'records/document_validation.json').write_text(json.dumps(out,indent=2,ensure_ascii=False));print(json.dumps(dict(status='PASS',checks=len(checks),documents=summaries),indent=2))
