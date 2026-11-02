"""Verify a downloaded v2.1.2-r0 test package without third-party dependencies."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def main():
 manifest=json.loads((ROOT/'MANIFEST.json').read_text());metadata=json.loads((ROOT/'RELEASE_METADATA.json').read_text());version=(ROOT/'VERSION').read_text().strip()
 errors=[]
 if not(version==manifest['version']==metadata['version']=='v2.1.2-r0'):errors.append('Package version mismatch')
 for row in manifest['files']:
  path=Path(row['path'])
  if path.is_absolute()or'..'in path.parts:errors.append('Unsafe manifest path');continue
  p=ROOT/path
  if not p.is_file():errors.append('Missing: '+str(path));continue
  if p.stat().st_size!=row['bytes']or sha(p)!=row['sha256']:errors.append('Changed: '+str(path))
 for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines():
  digest,name=line.split('  ',1);p=ROOT/name
  if not p.is_file()or sha(p)!=digest:errors.append('Checksum mismatch: '+name)
 for name in ['README.md','DATA_DIAGNOSTICS_INDEX.md','requirements-lock.txt','06_SUBMISSION/Manuscript.docx','06_SUBMISSION/Supplementary_Information.docx']:
  if not(ROOT/name).is_file():errors.append('Required package file absent: '+name)
 result={'status':'PASS'if not errors else'FAIL','version':version,'files_verified':len(manifest['files']),'manifest_sha256':sha(ROOT/'MANIFEST.json'),'errors':errors}
 print(json.dumps(result,indent=2))
 return int(bool(errors))
if __name__=='__main__':sys.exit(main())
