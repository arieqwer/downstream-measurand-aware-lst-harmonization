"""Compare rerun strict-quality results with baseline after <1 minute alignment."""
from pathlib import Path
import os,json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
WORK=Path(os.environ.get('LST_NATIVE_WORKSPACE',str(ROOT/'data/native_workspace')))
NEW=WORK/'auxiliary/quality/results';BASE=ROOT/'evidence/quality'
checks=[];cells=0
for old in BASE.glob('*.csv'):
    new=NEW/old.name
    if not new.exists():continue
    a=pd.read_csv(new);b=pd.read_csv(old)
    checks.append(dict(file=old.name,check='shape',passed=a.shape==b.shape))
    for c in a.columns.intersection(b.columns):
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
            x=a[c].to_numpy(float);y=b[c].to_numpy(float)
            checks.append(dict(file=old.name,check=c,passed=bool(np.allclose(x,y,atol=1e-10,rtol=1e-10,equal_nan=True))))
            cells+=len(x)
manifest=json.loads((NEW/'validation_manifest.json').read_text())
checks.append(dict(check='replayed baseline and independent controls',passed=all(v for k,v in manifest['acceptance'].items() if isinstance(v,bool))))
result=dict(status='PASS' if all(c['passed'] for c in checks) else 'FAIL',
            assertions=checks,numeric_cells_compared=cells,scope='Strict quality and paired5000draw sensitivity recomputed using newly reproduced calibration-only models; scientific results unchanged after primary <1minute scan-pair rule alignment.',failed=[c for c in checks if not c['passed']])
(NEW/'quality_reproduction_verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='assertions'},indent=2))
if result['status']!='PASS':raise SystemExit(1)
