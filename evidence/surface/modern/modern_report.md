# GOES 18 and 19 surface benchmark extension

29 October 2026. The extension is feasible as a **sampled recommended-quality raw-product benchmark** at the three existing SURFRAD sites. It is not strict-DQF-0 validation, full-period validation, or validation of the city-trained harmonization and urban core–ring workflow. No model, calibration action, uncertainty threshold or urban evaluation result was changed.

## Design and feasibility decision

The design was recorded before inspecting modern station residuals: the first local day of every one of the ten 2025 and eight 2026 study intervals, all ten target sunset-relative bins −3 through +6, Desert Rock/Fort Peck/Table Mountain, and the existing ground radiometry, quality and matching rules. The initial strict-DQF-0 pilot requested 60 station/platform rows on local 1 June 2026. All native and ground inputs were available, but there were zero common strict-quality pairs. Modern native metadata specify a 55° quantitative-quality view-angle threshold; all three GOES-19 station geometries exceed it.

A separate tier was therefore declared before residual inspection under the manuscript's existing modern primary rule, DQF 0 or 1 with physical LST bounds 180–380 K. This is explicit alignment with the study-product eligibility, not a threshold selected to improve temperature errors. The strict pilot remains unchanged. Its zero-support conclusion also holds across the complete modern sample. The declaration and rationale are in `acceptance_plan.md` and `recommended_quality_amendment.md`.

Meaningful-support criteria were fixed at ≥100 common pairs on ≥10 design dates and at least two sites with ≥20 pairs on ≥5 dates each. The completed sample passes: 282 common pairs on all 18 design dates, with 143/71/68 pairs at Desert Rock/Fort Peck/Table Mountain over 18/13/15 dates, respectively. This establishes adequate support for a bounded descriptive station comparison, not a representative sample of cities, climates or seasons.

## Inputs, quality, geometry and timing

There were 1,080 station/platform requests: 600 in 2025 and 480 in 2026. All 376 unique native LST files and 108 daily SURFRAD files are available. Initial transient TLS download failures were repaired by serial retry of the identical requests; first-attempt outputs and failure logs are retained. No failed transport was treated as scientific missingness or archive absence. All requested rows have 15 eligible ground minutes; none is lost to the ≥12-minute ground requirement. Native quality screening and joint eligibility determine retained matchups.

Civil-local-date sunset allocation is retained and checked for every request. Native sector scene midpoints approximate station-pixel acquisition times. The existing rule permits platform scan-start separation ≤60 s; observed retained separations are 0.1–6.4 s. Ground timestamps mark the ends of one-minute averages, so sample centers are shifted by −30 s. Upwelling/downwelling fluxes must both have QC=0 and be positive. The 15-minute ground window is centered on the native scene midpoint; at least 12 valid minutes are required.

Radiometric reference temperature is obtained from T=[(L↑−(1−ε)L↓)/(εσ)]^(1/4). Assumed published site emissivities remain 0.966/0.979/0.973 for Desert Rock/Fort Peck/Table Mountain. They are not contemporaneous measured emissivities. No city-trained correction is applied to station pixels.

Native sampled products identify v02r00. The GOES-19 station view angles estimated from projection geometry are 60.26° at Desert Rock, 62.56° at Fort Peck and 55.82° at Table Mountain. The corresponding GOES-18 angles are 47.88°, 63.37° and 56.69°. These are fixed nominal geostationary-geometry estimates, not instrument ephemeris reconstruction. Every one of the 540 GOES-19 station rows has the native PQI large-view flag, and none has DQF=0. GOES-18 has DQF=0 only at Desert Rock. The strict joint sample is therefore zero in both years. Per-site/year DQF 0/1/2/3 counts are retained in `quality_geometry_by_year_site.csv`.

Native pixel-center distances from the stations range 0.253–1.648 km; directional grid spacings range 2.335–4.492 km. A hemispherical local radiometer and a directional satellite pixel sample different supports. Terrain height and instantaneous satellite position are not used to refine the nominal angle estimates. These limitations preclude interpreting residuals solely as satellite retrieval error.

## Results on paired recommended-quality support

All quantities below use exactly the same retained station/time keys for both platforms within a year. Bias is satellite minus ground radiometric temperature, in kelvin.

| Year and site | Common pairs | Dates | G18 bias | G18 RMSE | G19 bias | G19 RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2025 Desert Rock | 84 | 10 | −0.989 | 1.493 | −2.223 | 2.725 |
| 2025 Fort Peck | 49 | 8 | +0.623 | 1.288 | +0.526 | 1.538 |
| 2025 Table Mountain | 40 | 9 | −2.750 | 2.995 | −2.762 | 3.186 |
| 2025 pooled | 173 | 10 | −0.940 | 1.904 | −1.569 | 2.573 |
| 2026 Desert Rock | 59 | 8 | −1.137 | 1.549 | −1.860 | 1.989 |
| 2026 Fort Peck | 22 | 5 | +0.150 | 1.351 | +0.178 | 0.979 |
| 2026 Table Mountain | 28 | 6 | −3.260 | 3.360 | −3.308 | 3.525 |
| 2026 pooled | 109 | 8 | −1.423 | 2.137 | −1.821 | 2.351 |

The G19-minus-G18 pooled RMSE difference is +0.669 K in 2025 and +0.214 K in 2026. With 5,000 crossed station–date bootstrap draws (seed 20261029), its 95% interval is −0.073 to +1.416 K in 2025 and −0.320 to +0.646 K in 2026. Both intervals include zero. With only three stations, they describe sparse-sample uncertainty rather than a population-wide platform ranking. Station–interval resampling is numerically identical because exactly one date was sampled per interval; it is not independent corroboration.

The original 2021 G16/G17 benchmark remains strict DQF=0. Its different product era, quality encoding, dates and retained supports prevent treating the historical and modern rows as a cross-era accuracy trend or ranking. The documented Desert Rock radiometry stability caveat remains a source-reported limitation; the modern residuals do not demonstrate that it has been resolved.

## Sensitivities

The imposed ε±0.01 scenarios yield pooled 2025 RMSE ranges 1.827–1.998 K for G18 and 2.456–2.701 K for G19; 2026 ranges are 2.029–2.261 and 2.203–2.509 K. Reference-temperature changes are at most 0.360 K in 2025 and 0.345 K in 2026. Uniform ε=0.97, nearest eligible ground minute, and separate ±5 W m⁻² upwelling/downwelling scenarios are retained. These are scenario perturbations, not complete probabilistic instrument-uncertainty bounds and not perturbations of ABI's actual retrieval-input emissivity.

A 3×3 recommended-quality neighborhood requires at least five eligible native pixels and matches both platforms on common neighborhood support. It retains 171 pairs in 2025 and 106 in 2026. The table `modern_neighborhood_sensitivity.csv` reports neighborhood and point metrics on those exact matched keys, so the comparison need not confuse pixel-support change with sample-selection change. Satellite footprint averaging does not establish spatial equivalence to the local radiometer.

## Executed independent checks and reproducibility

`modern_verification_summary.json` records **3,887 successful checks**. The independent script does not import the extraction implementation. It reads every retained ground ASCII window again, solves the energy balance using logarithms, replays every native point's CF decoding and DQF through netCDF4, reconstructs grid indices and native scene midpoint, and recomputes all primary metrics. Maximum differences: ground reference 2.27×10⁻¹³ K, primary metrics 8.88×10⁻¹⁶ K, native CF decoding 1.91×10⁻⁵ K (float32 CF versus float64 manual decoding). The negative control omitting reflected downwelling radiation correctly fails greybody recovery. The failed first independent run was a NumPy-bool JSON serialization issue after scientific calculations, preserved as `independent_modern_attempt1.log`; the corrected run passes.

The portable `scripts/reproduce_modern_offline.py` separately regenerates metrics, reference sensitivities, bootstrap intervals and neighborhood comparisons from packaged common pairs and retained neighborhood values. It contains no host-specific paths and needs only NumPy/Pandas. Its executed comparison against final outputs passes within 10⁻¹⁰ K absolute / 10⁻¹¹ relative tolerance. That offline command does **not** repeat native/ground decoding; those checks are executed here and retained with raw source manifests. The release clean-environment test should run that portable command again.

Executed commands use existing `/usr/bin/python3` with NumPy 2.0.2, Pandas 2.3.3, h5netcdf 1.8.1, netCDF4, PyProj, Astral and Requests. No environment installation was required.

```
python3 scripts/run_modern_surface.py --stage pilot
python3 scripts/run_modern_recommended.py --stage full
python3 scripts/retry_ground_serial.py --stage full --analyze-only
python3 scripts/summarize_verify_modern.py
python3 scripts/reproduce_modern_offline.py --data-dir recommended/results --output-dir offline_reproduction --verify-against recommended/results
```

Logs are task-root `pilot.log`, `recommended_full.log`, `retry_ground_serial.log`, `independent_modern.log`, and `offline_reproduction.log`, plus timestamped download/inventory/inputs/failure/run JSONL logs under the corresponding cache. Native and ground source CSVs retain provider URLs/object keys/hashes. No public release or submission occurred. Full urban-workflow ground validation remains incomplete, so R1-3 remains partially addressed.

## Compact manuscript treatment proposed to the coordinator

Methods: “A modern raw-product extension sampled the first local day of each of the ten 2025 and eight 2026 study intervals at the same three SURFRAD stations. It used the study's modern DQF 0–1 eligibility and the same radiometry, ground QC and matching rules. Strict DQF 0 yielded no common modern pairs because of the sites' viewing geometry and native quality assignments; the modern and historical quality tiers are therefore reported separately. Neither benchmark applies city-trained corrections.”

Results: “The modern recommended-quality sample retained 173 common pairs in 2025 and 109 in 2026. Pooled GOES-18/19 RMSE was 1.904/2.573 K and 2.137/2.351 K, respectively (Table S4). The 95% crossed station–date intervals for the GOES-19-minus-GOES-18 RMSE difference included zero in both years (−0.073 to +1.416 K; −0.320 to +0.646 K). Results varied by site and quality eligibility; these sampled station products do not validate the complete urban harmonization workflow.”

All detailed attrition, geometry, sensitivities and source manifests can reside in the repository rather than increasing the SI with additional notes/tables. The compact modern site rows can join the historical station table with explicit year, platforms and quality-tier labels.
