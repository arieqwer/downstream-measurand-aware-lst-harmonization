"""Independent post-run verification; never imports the benchmark implementation."""
from pathlib import Path
import os
PACKAGE_ROOT=Path(__file__).resolve().parents[2]
NATIVE_WORKSPACE=Path(os.environ.get("LST_NATIVE_WORKSPACE",str(PACKAGE_ROOT/"data/native_workspace"))).resolve()
import hashlib, json
import numpy as np
import pandas as pd
import netCDF4

B = NATIVE_WORKSPACE/'auxiliary/surface'
R = B / 'results'
f = pd.read_parquet(R / 'full_matchups_common.parquet')
allrows = pd.read_parquet(R / 'full_matchups_all.parquet')
req = pd.read_csv(R / 'full_requests_all.csv')
keys = ['station', 'design_date', 'target_hour']
assert len(f)>0 and len(f)%2==0 and f.groupby(keys).size().eq(2).all()
assert len(req)==1920 and len(allrows)+req.key.isna().sum()==1920
assert req.groupby('bucket').size().eq(960).all()
assert req.actual_sunset_local_date.eq(req.design_date).all()
assert f.point_dqf.eq(0).all() and f.ground_qc0_minutes.ge(12).all()

# Read original ASCII columns independently and center the reported averaging ends.
ground = {}
for station in sorted(f.station.unique()):
    parts = []
    for p in sorted((B / 'raw/surfrad' / station / '2021').glob('*.dat')):
        a = np.loadtxt(p, skiprows=2)
        t = pd.to_datetime(dict(year=a[:,0].astype(int), month=a[:,2].astype(int),
                                day=a[:,3].astype(int), hour=a[:,4].astype(int),
                                minute=a[:,5].astype(int)), utc=True)
        parts.append(pd.DataFrame({'mid':t-pd.Timedelta(seconds=30),
                                   'up':a[:,22], 'down':a[:,16],
                                   'ok':(a[:,17]==0)&(a[:,23]==0)&(a[:,16]>0)&(a[:,22]>0)}))
    ground[station] = pd.concat(parts).drop_duplicates('mid').sort_values('mid')

flux_error = temp_error = nearest_error = 0.0
for r in f.itertuples(index=False):
    t = pd.Timestamp(r.scan_mid)
    g = ground[r.station]
    g = g[g.ok & (g.mid > t-pd.Timedelta(seconds=450)) & (g.mid <= t+pd.Timedelta(seconds=450))]
    assert len(g) == r.ground_qc0_minutes
    up, down = g[['up','down']].mean()
    flux_error = max(flux_error, abs(up-r.lw_up_mean), abs(down-r.lw_down_mean))
    # Solve the greybody energy balance with logarithms, rather than calling production temp().
    emitted = (up-(1-r.literature_eps)*down)/r.literature_eps
    reference = np.exp((np.log(emitted)-np.log(5.670374419e-8))/4)
    temp_error = max(temp_error, abs(reference-r.ground_lst_k))
    n = g.iloc[np.argmin(abs((g.mid-t).dt.total_seconds()))]
    nearest = np.exp((np.log((n.up-(1-r.literature_eps)*n.down)/r.literature_eps)-np.log(5.670374419e-8))/4)
    nearest_error = max(nearest_error, abs(nearest-r.ground_nearest_lst_k))
assert flux_error < 1e-10 and temp_error < 1e-10 and nearest_error < 1e-10

# Independent native decoder on one valid matchup for each site/platform.
native_checks = []
for (station, bucket), g in f.groupby(['station','bucket']):
    r = g.sort_values('scan_start').iloc[0]
    with netCDF4.Dataset(r.native_path) as d:
        v = float(d.variables['LST'][int(r.row),int(r.col)])
        q = int(d.variables['DQF'][int(r.row),int(r.col)])
        assert q == 0 and abs(v-r.point_lst_k) < 1e-4
        assert pd.Timestamp(d.time_coverage_start) == pd.Timestamp(r.scan_start)
        native_checks.append({'station':station,'bucket':bucket,'CF_error_K':v-r.point_lst_k,
                              'path':r.native_path,'sha256':hashlib.sha256(Path(r.native_path).read_bytes()).hexdigest()})

metric_error = 0.0
reported = pd.read_csv(R / 'full_metrics.csv')
for r in reported.itertuples(index=False):
    z = f[f.bucket.eq(r.bucket)]
    if r.dimension != 'pooled':
        z = z[z[r.dimension].astype(str).eq(str(r.group))]
    assert len(z) == r.n
    e = z.point_lst_k.to_numpy()-z.ground_lst_k.to_numpy()
    for value, expected in [(e.mean(),r.bias),(np.linalg.norm(e)/np.sqrt(len(e)),r.rmse),(abs(e).mean(),r.mae)]:
        metric_error = max(metric_error, abs(value-expected))
assert metric_error < 1e-10

# Check percentile summaries against saved draws; do not generate another inferential run.
ci_error = 0.0
ci = pd.read_csv(R / 'raw_point_cluster_bootstrap_summary.csv')
for cluster in ci.cluster.unique():
    d = pd.read_parquet(R / f'raw_point_bootstrap_{cluster}.parquet')
    assert len(d) == 5000
    for r in ci[ci.cluster.eq(cluster)].itertuples(index=False):
        lo,hi = np.quantile(d[r.metric], [.025,.975])
        ci_error = max(ci_error,abs(lo-r.lower95),abs(hi-r.upper95))
assert ci_error < 1e-10

# Reconstruct all paired station temporal changes from common raw matchups.
tr = pd.read_csv(R/'station_pre_post_change.csv')
change_error = 0.0
for r in tr.itertuples(index=False):
    z = f[f.station.eq(r.station)&f.design_date.eq(r.design_date)&f.bucket.eq(r.bucket)]
    pre=z[z.target_hour.isin([-3,-2,-1])];post=z[z.target_hour.isin([4,5,6])]
    assert pre.target_hour.nunique()>=2 and post.target_hour.nunique()>=2
    delta=(post.point_lst_k-post.ground_lst_k).mean()-(pre.point_lst_k-pre.ground_lst_k).mean()
    change_error=max(change_error,abs(delta-r.residual_k))
assert change_error < 1e-10

# Negative control: ignoring reflected downwelling flux must not pass greybody recovery.
T=300.; eps=.966; down=300.; sigma=5.670374419e-8
up=eps*sigma*T**4+(1-eps)*down
incorrect=(up/(eps*sigma))**.25
assert abs(incorrect-T)>1
result={'status':'PASS within declared station-scale scope','common_pairs':len(f)//2,
        'raw_flux_mean_max_error_W_m2':flux_error,'ground_temperature_max_error_K':temp_error,
        'nearest_ground_minute_max_error_K':nearest_error,'native_CF_checks':native_checks,
        'metric_max_error_K':metric_error,'bootstrap_quantile_max_error_K':ci_error,
        'station_change_max_error_K':change_error,'negative_control_error_K':incorrect-T,
        'limitations':['Actual ABI pixel acquisition times are unavailable; scene midpoint is used.',
        'Three sites and four intervals do not validate city-area core/ring correction or global absolute accuracy.',
        'Emissivity is assumed, and ground/satellite spatial and angular supports differ.',
        'Civil-local-date sunset allocation is independently checked for all1920requests.']}
(R/'independent_surface_verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
