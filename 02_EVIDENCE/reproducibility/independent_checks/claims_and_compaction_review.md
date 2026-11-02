# Independent claims audit and compact SI plan

29 October 2026. This audit is read-only with respect to Word files, scientific inputs, existing models, thresholds and earlier evidence. All work is under this directory. It used the original manuscript/SI, both original reviewers, current tracked and accepted OOXML, all seven comments, the integration record and linked numerical evidence/code.

## Result and exact scope

**171/171 independent checks pass across the point/support and bootstrap audits. No material numerical error was identified.** The current corrected results remain the scientific baseline. The point/support evidence is `independent_claims_results.json` (143 checks), with exact input hashes, command, environment, all assertions and computed values. The actual executed command was:

```bash
/usr/bin/python3 '/Users/apple/Downloads/RS revision 1/continuation_20261029/science/claims_audit/independent_claims.py'
```

A separate independently implemented NumPy resampler executed 5,000 crossed city–interval draws for each of 2021 and 2026 (hourly and transition together), plus 5,000 paired strict-quality draws. All 28 mean/interval comparisons pass, with maximum absolute discrepancy 2.36×10−14 against the corrected retained summary tables. This actually regenerates these uncertainty quantities from per-observation inputs rather than checking copied summaries. Its evidence is `independent_bootstrap_results.json` and `independent_bootstrap_summary.csv`; command:

```bash
/usr/bin/python3 '/Users/apple/Downloads/RS revision 1/continuation_20261029/science/claims_audit/independent_bootstrap.py'
```

The independently regenerated 95% contrast RMSE-reduction intervals are −6.7521% to +6.4777% (2026 hourly), −0.7144% to +1.4421% (2026 transition), −4.2659% to +9.7953% (2021 hourly), and −12.2272% to +6.6206% (2021 transition). Paired strict-minus-recommended corrected hourly contrast RMSE has interval −0.181722 to +0.111492 K. The corresponding difference in correction MSE gain has interval −0.221975 to +0.025061 K². These uncertainty calculations condition on fitted models and retained support; quality intervals condition on the three strict-eligible cities.

The science runtime is the existing Python 3.9.6 / NumPy 2.0.2 / pandas 2.3.3 installation; document reads used the bundled document Python and lxml. No dependency was installed and no provider file downloaded for this audit.

This audit independently recomputed scalar quantities from corrected per-observation prediction Parquets, corrected paired-daily regional extracts and processed native cloud-scene rows. It independently reconstructed daily eligibility, common support, aggregation and transition keys. It did **not** re-extract all native NetCDF grids or refit calibration models, and does not claim those stages were independently re-executed. Native masking/decoding and selection scripts were inspected. The separate release and surface tasks have their own executed evidence.

An initial test used the usual default linear 90th-percentile interpolation and failed the radius check. Investigation of the original training implementation confirmed `quantile(0.9, interpolation="higher")`. Using that fixed documented method reproduces 1.504295530773343 K. This is a documentation precision issue, not a scientific repair or threshold change. The initial output and log are preserved as `independent_claims_attempt1_linear_quantile.*`; the final audit includes a negative control that rejects that default-linear result. Methods 2.4 should explicitly say **higher empirical quantile** so another implementation can reproduce the 186 supported cases exactly.

## Independently reconstructed material quantities

| Quantity | Direct recomputation | Interpretation |
| --- | --- | --- |
| 2021 residual correlation | 0.8859299656 → 0.5350185256 | Pooled discrepancy correlation, not physically identified sensor error correlation |
| 2021 within-hour covariance contribution | 0.2085208638 → 0.2085208638 K² | Unchanged for fixed hour-specific additive corrections |
| 2021 between-hour covariance contribution | 1.2282497084 → 0.0063933301 K² | Most pooled covariance loss is removal of a shared hourly-mean discrepancy pattern |
| 2021 total covariance | 1.4367705722 → 0.2149141939 K² | Sum of the preceding two weighted contributions |
| Differential offset at h=−3 | 0.5883857535 K | Direct core–ring contrast change from different offsets |
| Differential offsets h=+4,+5,+6 | 0.0981203527, 0.0931612512, 0.1179354504 K | Stronger pre-sunset differential correction |
| 2021 June only | n=1,330, two intervals, 69 cities; contrast RMSE0.625456→0.607325 K | Calendar dependence with historical offsets fixed; does not isolate LHP |
| 2026 contrast | n=5,716; RMSE0.804094→0.805258 K; netgain−0.0018724384 K² | No observed positive point gain |
| 2026 fixed residual radius | 1.5042955308 K | Higher empirical 90th percentile from corrected2025 raw-candidate out-of-fold residuals |
| Pooled 2026 directional | Coverage524/583=89.8799%; support186/583=31.9039%; agreement176/186=94.6237% | Both pooled criteria pass; agreement is conditional on supported cases |
| Original 2026 cohort | Coverage336/345=97.3913%; support100/345=28.9855%; agreement100/100 | Coverage exceeds85–95% band |
| Expansion 2026 cohort | Coverage188/238=78.9916%; support86/238=36.1345%; agreement76/86=88.3721% | Both diagnostic criteria fail |
| Modern recommended quality | 30,839 daily pairs;5,716 hourly;583 transitions;75 cities | Complete retained primary support |
| Modern strict quality | 883 daily pairs;215 hourly;21 transitions;3 cities | Conditional sparse subset; thresholds unchanged |
| Common-support strict minus recommended corrected contrast RMSE | 0.9042105−0.9492592=−0.0450487 K | Point difference; paired 95% interval independently regenerated separately, −0.181722 to +0.111492 K |
| Cloud sample | 32 platform acquisitions;8 first-local-day dates;target Phoenix hours−3/+4 | Region rows can have other cities’ sunset-relative bins |
| Cloud counts | Recommended676pairs/75 cities;clear588/74;1pixel573/74;2pixel547/73 | Scan-level sensitivity, not complete interval/transition validation |
| Two-pixel common-support comparison | Cloud raw/corrected0.962008/0.945884K;recommended on same547keys0.906556/0.916587K | Both selection and changed retained pixels influence aggregate comparisons |
| Reference contrast scale | Medianabsolute1.669792K2021,1.818256K2026;rawRMSEratios38.2365%,44.2234% | Aggregate discrepancy/signal scale comparison, not casewise percent error or true UHI accuracy |

Strict surviving cities are Tucson (uc_id 4843), South Valley (5428) and Albuquerque (5453). Their GOES-18 zenith angles are 46.9076°,51.8721°,51.9863°; GOES-19 angles 53.6093°,52.6668°,52.6073°. All lie near the low end of the full source-angle range 52.6073–72.2537°. This selection makes geography, source view angle and quality eligibility inseparable in the small strict sample. The conditional bootstrap resamples only those three cities and eight intervals; it must not be presented as a75-city robustness interval.

The quality runner currently allows a15-minute gap internally while primary Methods specify <1 minute. All actual retained gaps are <1 minute(max 0.983333), and independent reconstruction with the stricter documented rule leaves the exact same daily/hourly/transition supports. Align the portable runner to <1 minute to prevent future semantic drift; this does not change current results. The cloud pairing code already requires <60 seconds.

## Necessary targeted manuscript changes

The baseline already treats MSE decomposition as statistical accounting, preserves the June-only qualification, rejects full urban ground validation, and limits final-workflow spatial inference. Avoid broad rewriting. Make the following precise changes while replacing deleted SI-note references.

1. Abstract: use **post hoc corrected2026 temporal evaluation** at the first2026 result. Main 2.1 already explains previous outcome inspection and2025-only fitting. Preserve same75 cities and the uncertain contrast interval.
2. Main 2.4: specify the **higher empirical 90th percentile** of absolute2025 out-of-fold raw-transition residuals. Do not call this a conformal guarantee or fit another width.
3. Main 2.7/3.5: name the three strict cities, state that the paired bootstrap is conditional on those cities/eight intervals, and retain the21-transition deterioration in the compact screening table. Add that quality selection is coupled to geography/view angle. Do not infer75-city robustness.
4. Main 2.7: state modern DQF 0/high versus 1/medium if the terms are used; retain that historical bitmask semantics differ. Include cloud sampling (first local day of each of8 intervals,2 Phoenix-based acquisitions,32 platform scene pairs), original regional support thresholds and common support. Keep clear/cloud buffer support and scan-level labels.
5. Main 2.7 station methods: move the essential radiometry QC/timing details from old S9: both fluxes QC = 0; minimum 12 valid 1-minute measurements per 15-minute window; SURFRAD timestamps are averaging ends, so centers are 30 s earlier. Published emissivities are assumptions, not contemporaneous measurements. Keep reflected-downwelling-flux equation and nearest-native-pixel/DQF policy. Modern extension quality policy, if different, must be explicit and not presented as an identical crossera comparison.
6. Main 2.1: retain enough source-cohort provenance after removing old S1. Suggested addition after the existing observation-support definition: “The populations were inherited from a 5,541-city table whose grouping variable is the temporal mean count of daytime MODIS LST pixels with NDVI>0.30 in the ring. North American candidates were restricted to 24–50°N and 125–66°W; the higher-support pool additionally required complete morphology and water covariates and excluded 60earlier pilot cities.” Existing text already specifies the global-median split, western 51/43 candidates and44/31 analyzed groups. Exact median, source filenames, fields and full inventories belong in the repository.
7. Main 3.4/4.1: keep the total-covariance partition and its interpretation. The main currently does this accurately. Say “pooled discrepancy covariance” or “shared between-hour discrepancy pattern”; avoid implying removal of physically identified common sensor error. The invariance does not apply to the2026 core geometry model.
8. Main 4.3: keep the June-only numerical comparison and explicit **does not isolate LHP effects**. Add only a short availability sentence if oldNote S4is removed: historical sampled LST files lack the required thermal-state/mitigation series; missing objects are retained without attributing absence to LHP. Do not classify June as anomaly-free.
9. Main 3.3/Figure 5 caption/Discussion: retain pooled versus subgroup distinction,31.9% support,94.6% conditional agreement, original overcoverage and both expansion failures. Figure 5 caption can mention the original overcoverage explicitly while dropping repetitive prose elsewhere.
10. Main 4.1/4.3: retain the actual contrast-scale ratio and that ground-emissivity sensitivity is a reference-temperature scenario, not a perturbation of actual continuous ABI emissivity/NWP retrieval inputs. Matching ancillary metadata families does not establish equal numerical arrays.

All old Table S/Note S/Data S references must be remapped, not left dangling after compaction. Long future/general nonlinear-measurand discussion is optional to condense, but there is no scientific need for substantive further prose expansion.

## Compact SI recommendation

**Four numbered tables, zero Supplementary Notes, zero separately numbered Data attachments** is defensible. Table captions must still define units/denominators and restricted supports; eliminating necessary definitions would harm interpretability. Detailed data and diagnostics remain accessible in the prepared versioned repository, not discarded from the evidence.

| New item | Retain/merge | Reason |
| --- | --- | --- |
| S1 Exact MSE budgets | Old S4,10 rows | Supports central accounting across5 cohorts×2 measurands and distinguishes signed gain components |
| S2 Screening | Common-support hourly recommended/strict2 rows, common-support transition recommended/strict2 rows; cloud recommended/all,clear,1pixel,2pixel and recommended/common2pixel5 rows | Nine rows are sufficient. Main already gives complete baseline counts. Explicitly label hourly versus transition versus scan-pair units. Retain unfavorable strict transition values. |
| S3 Directional results | Old S9pooled/original/expansion3 rows only | Preserve n, covered n/%, supported n/%, matching n/%, criterion status; intervals detailed in repo |
| S4 Raw station products | Old S20site/pool4 rows; modern site/pool rows if rigorous extension succeeds | Site heterogeneity is necessary; do not retain only a favorable pooled metric. Different era/quality supports must be labeled. |

Old S1attrition and S2RMSE mostly duplicate mainTable1/Figure3; move detailed CSVs to repository. Old S3model scores andS8offsets can be repository outputs because main Methods/Figure 2 and 3.4state selection and offsets. Old S5–S7bootstrap/influence detail belongs in repository while main retains observed values/95%intervals and resampling methods. Old S10–S12dictionaries/inventory are repository documentation. Old S13–S17hour/geometry/calendar/PQI detail can be archived: main already gives central numbers and limitations. Old S18–S19merge into new S2. Old S20becomesnew S4; old S21radiometry sensitivities can be repository outputs with one concise main result/limits paragraph. All old S1–S9Notes disappear; essential content goes to the specific main sections listed above. Old Data S1–S20are repository files with a direct README mapping, not separate journal attachments.

There is no need to migrate every removed table into prose. The repository map and reproducibility package should retain every original detail and regenerated result, clearly organized as current corrected outputs. Historical old numbers must not remain active alternatives. No invented release URL/DOI should be inserted before the release exists.

## Seven comments and evidence-based resolution

| Existing anchor | Evidence/status | Recommended action |
| --- | --- | --- |
| Main comment 0post hoc preprocessing | Factually verified original protocol, corrected supports and2025-only radius; manuscript already explicit | Resolve factual verification after the new text is checked; keep post hoc wording in body. No renewed author scientific choice is needed to state this fact. |
| Main comment 1expansion failures | Independently rebuilt all denominators and criterion outcomes | Resolve factual verification after compactTable S3andmaincrossrefs match. Keep both failures and original overcoverage. |
| Main comment 2full urban validation | Existing station data cannot validate full urban workflow; user explicitly retains this boundary | Update/resolving the comment can record that boundary is now stated, but **R1-3 status remains partial**. Author approval of final reporting is distinct from experimental completion. |
| Main comment 3release | Local staging/integrity is not public publication | Keep open until user authorizes and actual versioned release is publicly accessible; no invented link. |
| SI comment 0gate | Same verified pooled/subgroup facts as main comment 1 | Resolve duplicate factual comment when new Table S3states them; move the explanation into main 2.4/3.3 rather than another SI Note. |
| SI comment 1ground benchmark | Same independent-station/fullworkflow boundary as main comment 2 | Resolve duplicate comment only after explicit main Methods/Discussion boundary and raw-product table are preserved; R1-3 still partial. |
| SI comment 2LHP | June subset calculation reproduced; metadata absence cannot establish anomaly-free scans | Resolve factual comment once main 4.3retains calendar-only interpretation and needed metadata limitation. |

None of these resolutions means accepting tracked suggestions. Full urban validation, unique physical causal attribution and final-selector unseen-city generalization remain unproven. Response-letter cross-checks are not complete because the user has explicitly deferred drafting; do not label the whole revision submission-ready.
