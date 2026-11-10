"""Verify the small public results package using the Python standard library."""
from pathlib import Path
import csv,hashlib,json,math,sys
ROOT=Path(__file__).resolve().parent

def main():
    manifest=json.loads((ROOT/'manifest.json').read_text())
    count=0
    for entry in manifest['files']:
        name=entry['path'];path=Path(name)
        assert not path.is_absolute() and '..' not in path.parts,name
        p=ROOT/path;assert p.is_file(),name
        assert p.stat().st_size==entry['bytes'],name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],name
        if p.suffix=='.csv':
            with p.open(newline='') as f:
                reader=csv.reader(f);header=next(reader);assert header,name
                for row in reader:assert len(row)==len(header),(name,row)
        count+=1
    with (ROOT/'results/exact_mse_budgets.csv').open(newline='') as f:
        budgets=list(csv.DictReader(f))
    for r in budgets:
        expected=float(r['component_variance_gain_k2'])+float(r['differential_bias_gain_k2'])-float(r['covariance_loss_penalty_k2'])
        assert math.isclose(expected,float(r['net_downstream_mse_gain_k2']),abs_tol=1e-10,rel_tol=1e-10),r
    with (ROOT/'cohorts/parent_city_inventory.csv').open(newline='') as f:assert len(list(csv.DictReader(f)))==5541
    with (ROOT/'cohorts/pilot_cities.csv').open(newline='') as f:assert len(list(csv.DictReader(f)))==60
    print(json.dumps({'status':'PASS','version':manifest['version'],'files_verified':count,'mse_budgets_checked':len(budgets),'scope':'File integrity, CSV structure, cohort inventory counts and exact MSE closure; no full model rerun implied'},indent=2))
    return 0
if __name__=='__main__':sys.exit(main())
