"""Tracked concision/additions against current proposal; no changes accepted."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from copy import deepcopy
from lxml import etree as E
import json,hashlib,sys
B=Path('/Users/apple/Downloads/RS revision 1');D=B/'concision_20261030'
sys.path.insert(0,str(B/'continuation_20261029/scripts'))
import edit_documents as PREVIOUS
H=PREVIOUS.H;resolve=PREVIOUS.resolve;N=H.N;q=H.q

def export(parts,root,path):
    pack=dict(parts);pack['word/document.xml']=H.xml(root)
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for n,v in pack.items():z.writestr(n,v)

def main():
    ledger=[];summaries=[]
    for doc,name,orig in [('manuscript','Manuscript v1_suggestions.docx','Manuscript v1.docx'),('si','supplementary_suggestions.docx','supplementary.docx')]:
        with ZipFile(D/'snapshots'/name) as z:parts={n:z.read(n) for n in z.namelist()}
        root=E.fromstring(parts['word/document.xml'])
        with ZipFile(B/orig) as z:original=E.fromstring(z.read('word/document.xml'))
        ps=root.xpath('//w:body//w:p',namespaces=N);origps=original.xpath('//w:body//w:p',namespaces=N)
        mapping={};ix=0
        for p in ps:
            if H.is_inserted(p):mapping[p]=None
            else:mapping[p]=origps[ix];ix+=1
        assert ix==len(origps),(doc,ix,len(origps))
        ids=root.xpath('//w:ins/@w:id|//w:del/@w:id|//w:pPrChange/@w:id',namespaces=N)
        H.counter=max(map(int,ids))+10000
        if doc=='manuscript':
            assert len(ps)==326,'Unexpected baseline paragraph map'
            ops=json.loads((D/'plans/manuscript_edits.json').read_text())
            for i,op in enumerate(ops):
                p=ps[op['p']];before=H.visible_text(p);assert before==op['before'],op['p']
                if not op['after']:
                    PREVIOUS.delete_paragraph(p,mapping[p])
                else:
                    np=H.replace_p(p,op['after'],mapping[p]);ps[op['p']]=np;mapping[np]=mapping[p]
                ledger.append(dict(id=f'CONC-M-{i+1:03d}',doc=doc,**op))
            # Reapply established body/link styles without altering equations,
            # reference identities, images or unrelated paragraphs.
            rels=E.fromstring(parts['word/_rels/document.xml.rels']);H.final_inserted_style(root,rels)
            parts['word/_rels/document.xml.rels']=H.xml(rels)
            # Concision moved the Table2 caption to a page bottom. Track its
            # keep-with-next property so it stays with the first table row.
            cap=ps[184];assert H.visible_text(cap).startswith('Table 2.')
            pp=cap.find(q('pPr'));oldpp=deepcopy(pp)
            assert pp.find(q('pPrChange')) is None
            if pp.find(q('keepNext')) is None:
                pp.insert(1 if pp.find(q('pStyle')) is not None else 0,E.Element(q('keepNext')))
            change=H.attrs(E.SubElement(pp,q('pPrChange')));change.append(oldpp)
            ledger.append(dict(id='CONC-M-FORMAT',doc=doc,p=184,before='Caption may break from its table',after='Keep caption with first table row',reason='Repair the orphaned Table2caption found in full rendered-page QA; native paragraph-format change remains unaccepted.',reviewers=['R2-M3']))
            # Replacing the DAS paragraph must preserve its one open author
            # comment rather than dropping the anchor with old paragraph text.
            if any(op['p']==261 for op in ops):
                cid='0';p=ps[261]
                assert not p.xpath('.//w:commentRangeStart',namespaces=N)
                p.insert(1,E.Element(q('commentRangeStart'),{q('id'):cid}))
                p.append(E.Element(q('commentRangeEnd'),{q('id'):cid}))
                rr=E.SubElement(p,q('r'));E.SubElement(rr,q('commentReference'),{q('id'):cid})
                cs=E.fromstring(parts['word/comments.xml']);assert len(cs)==1
                for t in cs.xpath('//w:t',namespaces=N):
                    if t.text:t.text=t.text.replace('v2.1.0-r1','v2.1.1-r1')
                parts['word/comments.xml']=H.xml(cs)
        else:
            body=root.find(q('body'));p=body.findall(q('p'))[10]
            before=H.visible_text(p)
            intro=json.loads((D/'plans/si_addition.json').read_text())['intro']
            np=H.replace_p(p,intro,mapping[p]);mapping[np]=mapping[p]
            specs=json.loads((D/'plans/si_addition.json').read_text())
            spec=specs['table']
            # Insert after the existing fourth proposal table, before the
            # original SI's tracked deletions. Existing four tables are intact.
            active_tables=[t for t in body.findall(q('tbl')) if t.xpath('./w:tr[w:trPr/w:ins]',namespaces=N)]
            assert len(active_tables)==4
            at=body.index(active_tables[-1])+1
            cap=H.paragraph(spec['caption'],'MDPICaption')
            pp=cap.find(q('pPr'));rp=pp.find(q('rPr'));pp.insert(pp.index(rp),E.Element(q('pageBreakBefore')))
            tab=PREVIOUS.table(spec['headers'],spec['rows'],spec.get('widths'))
            body.insert(at,cap);body.insert(at+1,tab)
            ledger.extend([dict(id='CONC-SI-001',doc=doc,before=before,after=intro,reason='Update concise inventory for one compact principal-diagnostics table.',reviewers=['R2-M6','R2-M3']),dict(id='CONC-SI-002',doc=doc,before='',after=spec,reason='Expose principal hour and VZA evidence with sample sizes and signed MSE budgets in one table.',reviewers=['R2-M6'],sources=specs['sources'])])
        export(parts,root,B/name)
        for accept,label in [(True,'accepted'),(False,'rejected')]:
            view=resolve(root,accept);H.strip_comments(view)
            export(parts,view,D/'qa'/f'{doc}_{label}.docx')
            if accept:
                rec=[dict(p=i,text=H.txt(p),style=p.xpath('./w:pPr/w:pStyle/@w:val',namespaces=N)) for i,p in enumerate(view.xpath('//w:body//w:p',namespaces=N))]
                (D/'records'/f'{doc}_accepted.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False))
                (D/'records'/f'{doc}_accepted.txt').write_text('\n'.join(p['text'] for p in rec))
        summaries.append(dict(doc=doc,path=str(B/name),sha256=hashlib.sha256((B/name).read_bytes()).hexdigest()))
    (D/'records/change_ledger.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False))
    (D/'records/authoring_summary.json').write_text(json.dumps(summaries,indent=2))
    print(json.dumps(summaries,indent=2))

if __name__=='__main__':main()
