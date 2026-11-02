# R1 revision completion record for author review

30 October 2026. This is an internal evidence and decision record, not a reviewer response letter. It supplements and supersedes the open-task status and old SI numbering in [the 29 October integration record](../02_EVIDENCE/reproducibility/history/Revision_integration_record_20261029.md). That record preserves the original reviewer wording and earlier repair history; [the current coverage ledger](../02_EVIDENCE/reproducibility/document_checks/reviewer_coverage_final.tsv) supplies the current disposition of all 16 comments.

## Current review files and completion status

- [Manuscript with native unaccepted Track Changes](Manuscript%20v1_suggestions.docx)
- [SI with native unaccepted Track Changes](supplementary_suggestions.docx)
- The original manuscript, SI and combined reviewer-comment document are unchanged. Pre-continuation suggestions and original hashes are preserved in [the baseline manifest](../02_EVIDENCE/reproducibility/document_checks/baseline_manifest.json) and `snapshots/`.
- Scientific/document checks and local release preparation are complete within the study scope. Author review, public release authorization/publication, final Data Availability update and reviewer response letters/cross-checks remain. **The revision is not declared submission-ready.** No public push, deposit, release, email or journal submission was made.
- All proposed Word edits remain unaccepted. Six anchored comments were resolved through verified facts or the user's stated scope; the release comment remains open. Resolving the ground-validation reporting comments does not complete R1-3 scientifically.

## What was independently checked

The original and integrated documents, all existing changes/seven comments, both reviewers, the integration record and linked ledgers, repaired per-observation inputs/predictions, native diagnostics, source/figure functions and staged public-repository layout were inspected. Existing corrected results were treated as the baseline and material claims were recomputed rather than merely copied. Raw provider/source inputs and both original documents remained immutable. No material numerical error was found in the corrected baseline. The existing local-sunset-date and complete-polygon repairs remain intact; no 2026 outcomes entered fitting/selection and no criteria were tuned to improve subgroups.

Acceptance checks were specified before the expanded checks in [the acceptance plan](../02_EVIDENCE/reproducibility/document_checks/acceptance_plan.md). Evidence distinguishes independent scalar/bootstrap reconstruction, native/raw radiometry verification, clean processed-data reruns and retained figure inputs. The claim audit also retains a failed default-linear-quantile negative control: the original method uses the **higher empirical 90th percentile**, which reproduces the fixed 1.5042955308 K half-width and 186 supported transitions. Clarifying this rule changes no result.

## Ground validation and modern extension

The existing independent raw-product GOES-16/17 benchmark is retained: 413 common station/time pairs at Desert Rock, Fort Peck and Table Mountain during four 2021 windows. Pooled RMSE is 4.678/4.094 K and bias is −3.249/−3.110 K; large Desert Rock residuals and all sites remain visible.

The GOES-18/19 extension was feasible with existing code after an explicit quality-support assessment. A strict DQF-0 pilot found **zero joint pairs**. Before modern residual inspection, a separate recommended-quality tier was specified using the study's existing modern DQF0–1 policy; it does not alter the strict benchmark or urban quality robustness experiment. The original strict failure is retained. Meaningful-support criteria (at least 100 pairs, ten dates and two sites with at least 20 pairs on five dates) were fixed before results and passed.

Sampling covered the first local day of each of ten 2025 and eight 2026 study intervals, the same three stations and ten sunset-relative bins. All 1,080 station/platform requests were available after recorded transient network retries, involving 376 distinct LST objects and 108 SURFRAD daily files. Ground QC, reflected downwelling radiation, published assumed emissivity, minimum minute support and actual scene-time matching were checked. SURFRAD averaging-end timestamps were shifted back 30 seconds. Both platform actual scan starts differ by less than 60 seconds (maximum retained gap 6.4 s).

| Modern common support | 2025 | 2026 |
| --- | ---: | ---: |
| Common pairs | 173 | 109 |
| Desert Rock / Fort Peck / Table Mountain | 84 / 49 / 40 | 59 / 22 / 28 |
| GOES-18 RMSE (K) | 1.904 | 2.137 |
| GOES-19 RMSE (K) | 2.573 | 2.351 |
| GOES-18 bias (K) | −0.940 | −1.423 |
| GOES-19 bias (K) | −1.569 | −1.821 |
| 95% crossed station–date interval for G19 minus G18 RMSE (K) | −0.073 to +1.416 | −0.320 to +0.646 |

There are 282 pairs on 18 dates. All retained GOES-19 pixels are DQF1 and carry the large-view-angle flag; GOES-19 view zenith spans 55.82–62.56°, and GOES-18 47.88–63.37°. Strict joint support remains zero. Both RMSE-difference intervals include zero. Different quality policies and temporal support preclude historical-versus-modern skill ranking. Three sparse stations and selected first days do not represent the full regional/time population, area-average urban cores/rings or complete transitions. No urban-trained correction was applied to station pixels. **R1-3 remains partially addressed.**

Assumed emissivity ±0.01, uniform 0.97, imposed ±5 W m−2 longwave scenarios, nearest-minute matching and 3×3 satellite neighborhoods were evaluated. These ground-reference/spatial-support scenarios do not perturb actual ABI retrieval emissivity or atmospheric arrays. Full methods/results, support manifests and exclusions are in [the modern report](../02_EVIDENCE/surface/modern/modern_report.md). Essential procedures/results are in Methods 2.7, Results 3.5, Discussion 4.3 and compact SI S4.

## Covariance, quality and physical interpretation

The historical residual correlation independently reproduces as 0.8859299656→0.5350185256. The observation-weighted within-hour covariance contribution is unchanged at 0.2085208638 K² under fixed hour-specific additive shifts. The between-hour contribution falls from 1.2282497084 to 0.0063933301 K², giving total covariance 1.4367705722→0.2149141939 K². Differential offsets alter contrast by 0.5884 K at h=−3 and approximately 0.093–0.118 K at h=+4…+6. This is an algebraically identified change in pooled discrepancy structure, not uniquely identified physical common sensor error. The invariance argument is specific to the historical hour-offset operation and is not imposed on the 2026 geometry model.

The June-only fixed-offset sensitivity retains 1,330 hourly rows at 69 cities and yields contrast RMSE 0.6255→0.6073 K, net MSE gain 0.0224 K². Removing entire July intervals changes season, weather and support; June is not classified as anomaly-free. Missing thermal-state/mitigation fields and archive missingness do not diagnose LHP state. Methods/Discussion explicitly retain that distinction.

Strict DQF0 sensitivity retains **Tucson, South Valley and Albuquerque only: 883 daily pairs, 215 hourly means and 21 transitions**. The paired bootstrap conditions on those three cities/eight intervals. The cities lie near the low source-view-angle end of the full population, so geography, viewing geometry and quality eligibility cannot be separated here. On common daily support, strict transition contrast RMSE worsens 0.8160→0.8399 K. The evidence cannot support 75-city quality robustness. Thresholds were not relaxed.

Cloud-mask diagnostics use 32 matched platform acquisitions on the first local day of eight intervals, initially selected at Phoenix bins−3/+4; other cities have their own sunset bins. Counts are 676 recommended scan pairs, 588 clear, 573 one-pixel-buffer and 547 two-pixel-buffer pairs. Common-support comparisons and changed pixel composition are distinguished. These are selected scan sensitivities, not full-period or full-transition validation. Native ancillary-family/quality metadata and geometry strata are observational diagnostics, not proof of equal numerical ancillary inputs or physical source attribution.

The discrepancy/signal comparison uses the actual reference median absolute core–ring contrast: 1.670 K (2021) and 1.818 K (2026), with raw contrast RMSE approximately 38.2% and 44.2% of those scales. These are aggregate scale comparisons, not casewise relative errors, independent UHI truth or a generic 2–5 K assumption.

## Temporal transfer and unfavorable findings

The corrected 2026 analysis uses the same 75 cities as 2025 calibration. It is a **post hoc corrected temporal evaluation under the original model-selection protocol** because earlier outcomes had been inspected. Earlier spatial/platform transfer tests do not establish unseen-city generalization of the final selector. That final-workflow test remains unperformed.

- Core/ring RMSE improves 1.748→0.705 K and 1.506→0.662 K. Component-derived contrast changes 0.804094→0.805258 K: −0.14% RMSE reduction, 95% city–interval interval −6.75% to +6.48%. No established contrast improvement is claimed.
- Pooled transition coverage is 524/583=89.9%. Only 186/583=31.9% receive sign support; 176/186=94.6% of those agree with the satellite reference. Conditional agreement is not support for 94.6% of all transitions.
- Expansion coverage 188/238=79.0% and agreement 76/86=88.4% fail both fixed criteria. Original coverage 336/345=97.4% exceeds the 85–95% band; its supported agreement is 100/100. All remain explicit in main 3.3/Figure 5 and SI S3.
- Direct measurand selection retains raw contrast/transition; component-derived results are reported separately. No 2026-based fitting, threshold retuning or favorable subset replacement was undertaken.

## SI compaction and exact change record

The proposed SI is **four tables, zero Notes, zero separately numbered Data attachments**, rendered in three clean pages (20 before this continuation). The delivered file shows 16 pages with deletions visible because Track Changes remains unaccepted. Deletion visibility is not the proposed SI length. Captions retain necessary units, supports and denominators.

| Current SI item | Necessary publication content | Detailed information retained elsewhere |
| --- | --- | --- |
| S1 | Ten exact MSE budgets across five evaluation cohorts and hourly/transition quantities | Full budgets, draws, bootstrap summaries and influence outputs in repository |
| S2 | Nine common-support quality and sampled cloud rows, including unfavorable transition results | Full diagnostics and conditional bootstrap evidence in repository; procedures in main 2.2/2.7 |
| S3 | Pooled/original/expansion counts, coverage, support, agreement and failures | Full interval-level summaries in repository; fixed rule and interpretation in main 2.4/3.3 |
| S4 | Twelve historical/modern site and pooled raw-product rows | Complete timing/QC/radiometry/ancillary/sensitivity data in repository; procedures in main 2.7 |

Old attrition/RMSE tables duplicate main Table 1/Figures; detailed model scores, offsets, bootstrap draws, hour/geometry/calendar/PQI strata and dictionaries are repository evidence. Essential parent-cohort, pairing, native-quality/cloud and ground-reference procedures are integrated directly in Methods 2.1/2.2/2.6/2.7. All old SI Note/Data references are removed from the proposed manuscript. [The exact before/after ledger](../02_EVIDENCE/reproducibility/document_checks/change_ledger.json) records31 main operations plus SI compaction; correct prior revisions remain.

| New change ID | Current manuscript anchor | Reviewer IDs | Reason |
| --- | --- | --- | --- |
| CONT-M-001 | Front matter / Abstract; paragraph 22 | R2-M5 | State corrected temporal status at the first Abstract result. |
| CONT-M-002 | 2.1. Study Design and Evaluation Cohorts; paragraph 34 | R2-M3 | Move essential cohort provenance into Methods and detailed sources to repository. |
| CONT-M-003 | 2.1. Study Design and Evaluation Cohorts; paragraph 34 | R2-M3 | Replace SI Note S1 with essential provenance in Methods; full census and code remain archived. |
| CONT-M-004 | 2.1. Study Design and Evaluation Cohorts; paragraph 36 | R2-M3, R2-M5 | Replace removed SI dictionary/data numbering with canonical archived chronology. |
| CONT-M-005 | 2.1. Study Design and Evaluation Cohorts; paragraph 41 | R2-M3 | Remove redundant SI inventories while retaining exact source records. |
| CONT-M-006 | 2.2. Satellite Data and Cross-Platform Pairing; paragraph 114 | R1-1, R2-M6 | Document primary eligibility and era-specific semantics directly in Methods. |
| CONT-M-007 | 2.2. Satellite Data and Cross-Platform Pairing; paragraph 115 | R1-1, R2-M6 | Remove Note and detailed PQI table; preserve attribution boundary. |
| CONT-M-008 | 2.2. Satellite Data and Cross-Platform Pairing; paragraph 116 | R2-M3 | Remove SI metadata dictionary duplication. |
| CONT-M-009 | 2.2. Satellite Data and Cross-Platform Pairing; paragraph 118 | R1-1, R2-M6 | Preserve geometry diagnostic method in main text. |
| CONT-M-010 | 2.3. Downstream Measurands and Harmonization Model Selection; paragraph 130 | R2-M2, R2-M3 | Model-selection figure and main methods retain essentials; full numerical scores move to repository. |
| CONT-M-011 | 2.4. MSE Decomposition and Measurand-Level Decisions; paragraph 145 | R2-M6 | Renumber retained exact MSE budget table. |
| CONT-M-012 | 2.4. MSE Decomposition and Measurand-Level Decisions; paragraph 150 | R2-M5, R2-M6 | Document the actual existing empirical quantile convention; no threshold or results change. |
| CONT-M-013 | 2.6. Statistical Uncertainty and Implementation; paragraph 156 | R2-M3, R2-m3 | Move complete resampling tables and diagnostic draws out of SI. |
| CONT-M-014 | 2.6. Statistical Uncertainty and Implementation; paragraph 157 | R2-M4, R2-M6 | Retain methods and main findings; archive detailed strata without Notes. |
| CONT-M-015 | 2.6. Statistical Uncertainty and Implementation; paragraph 158 | R2-M3 | Replace 20-entry SI inventory with versioned release manifest. |
| CONT-M-016 | 2.7. Native-Product Sensitivities and Surface Benchmark; paragraph 160 | R2-M6 | Integrate essential former Notes S7–S8 directly into Methods; define fixed support and conditional uncertainty. |
| CONT-M-017 | 2.7. Native-Product Sensitivities and Surface Benchmark; paragraph 161 | R1-3, R2-M1 | Move essential ground-radiometry, QC, timing and common-support procedures from Note S9 into Methods. |
| CONT-M-018 | 2.7. Native-Product Sensitivities and Surface Benchmark; paragraph 161 | R1-3, R2-M1, R2-M6 | Modern extension: predeclared recommended-quality tier, fixed sampling/ground rules and strict feasibility failure. |
| CONT-M-019 | 2.7. Native-Product Sensitivities and Surface Benchmark; paragraph 161 | R1-3, R2-M6 | Replace Note S9 with necessary methods and explicit distinction between ground and ABI-input sensitivity. |
| CONT-M-020 | 2.7. Native-Product Sensitivities and Surface Benchmark; paragraph 164 | R2-M3 | Avoid redundant SI RMSE table; primary figures/text preserve results. |
| CONT-M-021 | 3.3. Corrected 2026 Measurand-Level Decisions; paragraph 180 | R2-M5, R2-M6 | Keep concise three-cohort directional table; archive interval details. |
| CONT-M-022 | 3.3. Corrected 2026 Measurand-Level Decisions; paragraph 221 | R2-M6 | Covariance partition is already explicit in main Results. |
| CONT-M-023 | 3.4. Historical GOES-17/GOES-16 Replication; paragraph 222 | R2-M6 | Keep differential offset mechanism and invariance explanation in main; archive full strata. |
| CONT-M-024 | 3.4. Historical GOES-17/GOES-16 Replication; paragraph 227 | R2-M6 | Name restricted strict population and its geographic/geometry selection; retain all negative and conditional findings. |
| CONT-M-025 | 3.4. Historical GOES-17/GOES-16 Replication; paragraph 228 | R1-3 | Retain independent historical benchmark with compact station table. |
| CONT-M-026 | 3.5. Screening and Independent Surface Comparisons; paragraph 235 | R1-1, R2-M6 | Keep quantitative quality/geometry association in main after archiving the detailed PQI table; no causal claim. |
| CONT-M-027 | 4. Discussion; paragraph 236 | R2-M6 | Scale comparison and near-zero warning are already complete in main Discussion. |
| CONT-M-028 | 4.2. Transfer Across Cities, Periods, and Platform Pairs; paragraph 249 | R2-M4 | Move essential LHP metadata and calendar limit from Note S4 into Discussion. |
| CONT-M-029 | 4.3. Limitations and Transfer Boundaries; paragraph 254 | R2-M3, R2-M6 | Reduce SI to four substantive tables, no Notes and no separately numbered Data attachments. |
| CONT-M-030 | 3.4. Historical GOES-17/GOES-16 Replication; paragraph 228 | R1-3, R2-M1 | Modern extension: integrate verified multi-site raw-product result, sparse-sample uncertainty and quality limitations. |
| CONT-M-031 | 5. Conclusions; paragraph 257 | R2-M3 | Describe verified existing repository and prepared local version without claiming a published corrected release or inventing a URL/DOI. |

Paragraph indices above are internal zero-based accepted-view OOXML anchors for reproducibility, not journal line numbers. Final response-letter line numbers must be regenerated from the author-approved final Word layout. Existing historical locators in the29 October record are superseded.

## Disposition of seven author comments

- **main comment 0 — Post hoc preprocessing repair: Resolved factual check.** Calibration-only fitting and prior 2026 outcome inspection independently verified; post hoc and same-city boundaries retained in body.
- **main comment 1 — Expansion subgroup failures: Resolved factual check.** Both failures and original overcoverage independently rebuilt and retained in Results 3.3, Figure 5 caption and SI S3.
- **main comment 2 — Full urban validation: Resolved reporting comment; scientific gap remains.** User-directed boundary and raw-product scope are explicit; modern extension strengthens partial evidence but R1-3 remains partial.
- **main comment 3 — Public corrected release: OPEN: author authorization and actual publication required.** Local v2.1.0-r1 is prepared. No public release exists for it; DAS remains truthful future/status wording.
- **si comment 0 — Directional gate: Resolved duplicate factual check.** New S3 and main 2.4/3.3 retain fixed criteria, denominators and failures; old Note removed by compaction.
- **si comment 1 — Ground benchmark: Resolved duplicate reporting comment; scientific gap remains.** Essential ground methods integrated in 2.7; all station/site results in S4; full urban validation limitation retained.
- **si comment 2 — LHP calendar limitation: Resolved factual check.** June-only result verified; main 4.3 states it does not isolate LHP and records missing thermal-state evidence.

No change was accepted to resolve a comment. [The comment disposition ledger](../02_EVIDENCE/reproducibility/document_checks/author_comments_disposition.json) retains the original IDs and reasoning. The independent station/raw-product limitation remains in the body after removal of duplicate comments.

## Comment-by-comment review coverage

### R1-1 — Addressed with bounded diagnostic evidence

**Where:** Introduction; Methods 2.1–2.2/2.7; Results 3.4–3.5; Discussion 4.1/4.3

**Changes:** Clarified downstream consistency as the objective; retained reference uncertainty, retrieval-era/ancillary metadata, unequal viewing geometry, hour, quality and sampled cloud diagnostics. Added the modern station comparison and explicit support restrictions.

**Remaining boundary / recommendation:** Pixel-level physical attribution and equality of numerical ancillary arrays are not established; no new retrieval pipeline is warranted for these claims.

### R1-2 — Addressed editorially

**Where:** Methods 2.1–2.7

**Changes:** Retained the dependency-ordered methods structure. Integrated essential cohort, DQF, cloud and surface procedures into Methods while removing all SI Notes and updating every SI cross-reference.

**Remaining boundary / recommendation:** Review the proposed text for author preference; no additional experiment is needed.

### R1-3 — Partially addressed; full urban workflow ground validation incomplete

**Where:** Methods 2.7; Results 3.5; Discussion 4.3; Conclusions; SI S4

**Changes:** Retained 413 historical GOES-16/17 station pairs and added 282 GOES-18/19 common station/time pairs on 18 sampled dates at the same three SURFRAD sites. Reported all sites, quality policies, ground assumptions, timing, viewing geometry, uncertainty and sensitivities. No city correction was applied to station pixels.

**Remaining boundary / recommendation:** Full-process urban core/ring/transition validation requires matched area-representative ground observations not supplied by these stations. Recommend submitting the independent raw-product benchmark with this explicit limitation, rather than claiming full resolution.

### R1-4 — Addressed

**Where:** Figure 6; Results 3.5

**Changes:** Retained the corrected physical-local-date Phoenix native LST spatial fields, actual times, geographic extent, quality gaps and polygon outlines. Independently regenerated Figure 6 from retained decoded native arrays and verified identical pixels.

**Remaining boundary / recommendation:** Illustrative sampled spatial fields are not cloud-free truth; a new scene was not selected to improve appearance.

### R2-M1 — Addressed by consistency framing and independent raw-product evidence

**Where:** Title; Abstract; Methods 2.1–2.2/2.7; Results 3.5; Discussion 4.3; SI S4

**Changes:** Preserved the distinction between relative consistency and absolute accuracy, reference-platform rationale/error, historical thermal limitations and independent historical station evidence; extended the raw-product comparison to the modern platforms.

**Remaining boundary / recommendation:** Neither universal reference superiority nor absolute accuracy of the urban harmonization workflow is demonstrated.

### R2-M2 — Addressed

**Where:** Introduction; Methods 2.3–2.4; Discussion 4.1–4.2; reference 26

**Changes:** Retained attribution of the MSE identity, cross-validation and one-standard-error rule to established methods. The contribution is the combined downstream decision workflow and its evaluation, including raw retention and directional abstention.

**Remaining boundary / recommendation:** No newly invented decomposition or statistical selection algorithm is claimed.

### R2-M3 — Editorial/provenance work complete locally; public release pending

**Where:** Methods 2.1; manuscript Supplementary Materials/Data Availability; SI; release documentation

**Changes:** Added essential provenance of the 5,541-city parent collection and inherited eligibility/grouping to Methods. Reduced the SI from 21 tables, nine Notes and 20 numbered Data attachments to four tables and zero Notes/Data attachments; full corrected computational detail is retained in the staged repository. Clean SI preview is three pages, versus 20 before this continuation.

**Remaining boundary / recommendation:** The public repository still needs the author-approved versioned update. No overall manuscript word-count reduction is claimed.

### R2-M4 — Consistency reframing complete; LHP response remains bounded

**Where:** Methods 2.2/2.6; Discussion 4.3; repository calendar/native evidence

**Changes:** Retained the LHP discussion and reference/hour-offset implications. Independently verified the fixed-offset June-only result (1,330 hourly rows; contrast RMSE 0.6255→0.6073 K; net gain 0.0224 K²) and described the missing thermal-state/mitigation evidence in the main text.

**Remaining boundary / recommendation:** June-only exclusion does not isolate or eliminate LHP effects. No causal thermal-state classification is claimed; retain this limitation rather than reconstruct telemetry.

### R2-M5 — Addressed through corrected inference and transparent unfavorable results

**Where:** Abstract; Methods 2.1/2.4; Results 3.3; Figure 1/5; Discussion 4.2–4.3; SI S3

**Changes:** All relevant claims identify the same 75 cities in 2025 and 2026 and a post hoc corrected temporal evaluation under the original protocol. Retained uncertain contrast performance, both expansion directional failures, original overcoverage, and 31.9% sign support separately from 94.6% conditional agreement. Specified the existing higher empirical quantile without changing the threshold.

**Remaining boundary / recommendation:** Final-selector performance at entirely unseen cities remains untested; earlier spatial-transfer stages do not independently establish it. No additional city cohort is recommended for the present bounded claim.

### R2-M6 — Quantitative diagnostics completed within scope; physical attribution partial

**Where:** Methods 2.2/2.4/2.6–2.7; Results 3.2–3.5; Discussion 4.1/4.3; SI S1–S4

**Changes:** Independently reproduced residual correlation and within-/between-hour covariance, differential offsets, hour and geometry strata, strict DQF/common support, sampled cloud screening, native ancillary metadata and ground sensitivities. Strict results explicitly concern Tucson, South Valley and Albuquerque only (215 hours/21 transitions); geographic/view-angle dependence and conditional bootstrap are explicit. Compared discrepancy RMSE with actual reference contrast medians, retaining 38.2%/44.2% aggregate scale ratios.

**Remaining boundary / recommendation:** Statistical covariance accounting is not unique physical attribution. Ground-emissivity perturbations do not alter actual ABI retrieval inputs. Cloud diagnostics cover selected scans on eight dates; strict quality is not 75-city robustness.

### R2-m1 — Addressed

**Where:** Methods equations (1)–(12)

**Changes:** Verified 12 numbered editable main equations, preservation of original math, and current references after compaction.

**Remaining boundary / recommendation:** Refresh final page/line locators after author decisions.

### R2-m2 — Addressed

**Where:** Highlights

**Changes:** Retained four concise bullets under the journal-style two questions, including corrected component/contrast ranges and scientific implication.

**Remaining boundary / recommendation:** No unrelated journal or 85-character limit was imposed.

### R2-m3 — Addressed

**Where:** Abstract; Methods 2.6–2.7; captions

**Changes:** Defined independent city/interval resampling at first use and standardized crossed city–interval bootstrap. Modern station intervals use crossed station–date resampling, with their separate fixed seed stated.

**Remaining boundary / recommendation:** Keep station-date and city-interval uncertainty designs distinct in future response letters.

### R2-m4 — Addressed

**Where:** Figure 1b and caption

**Changes:** Retained land/water, coastline and state/province boundaries in the traced regenerated map; verified all six current figures reproduce exactly.

**Remaining boundary / recommendation:** No speculation is made about which earlier figure version the reviewer saw.

### R2-m5 — Addressed with documented metadata-check scope

**Where:** References; numeric citations

**Changes:** Preserved visible reference normalization and 34-entry citation identity/order; prior primary-source metadata checks for added references are retained. The final Word audit checks citation range, duplicates and identities.

**Remaining boundary / recommendation:** Not every unchanged old reference has received a new independent metadata lookup in this continuation.

### R2-m6 — Addressed

**Where:** Methods 2.1

**Changes:** Retained the clarified ~11.1 km nominal reduction scale (11,132 m in Earth Engine) on the distributed 0.1° grid, distinguishing scale parameter from spatial cell dimensions.

**Remaining boundary / recommendation:** No underlying ERA5-Land rerun is needed for this wording clarification.

## Executed reproducibility checks and their limits

| Executed check | Result | Scientific scope |
| --- | --- | --- |
| Independent point/support reconstruction |143/143 PASS | Per-observation budgets/covariance, daily/common support, gates, cloud rows and scales |
| Independent5,000-draw uncertainty reconstruction |28/28 PASS; max absolute difference2.36×10−14 | Historical/2026 crossed draws plus paired strict-quality draws; conditional on models/support |
| Modern raw/native/ground audit |3,887 checks PASS | Reopened provider files, CF/grid/radiometry/minute-QC/matching and metrics; not urban validation |
| Fresh isolated processed-data package rerun |1110 checks PASS;4,137,623 numerical cells;39 CSV and18 Parquet comparisons | All12 processed datasets, calibration/model selection, evaluation, bootstraps, budgets, gates and tables |
| Figure reproduction |6/6 pixel-identical |2–5 use rerun numerical outputs;1 uses fixed metadata/basemaps;6 uses retained decoded native arrays |
| Fresh isolated strict-quality rerun |PASS | Existing fixed criteria and fitted models; three-city conditional population |
| Fresh isolated modern offline reconstruction |4 output-table comparisons PASS; max difference1.33×10−15 |282packaged pairs;16 metric rows,36 sensitivity rows,12 interval rows,4 neighborhood rows; raw decoding not repeated here |
| Final Word scientific/content audit |256 checks PASS;156 numeric cells matched | Four SI tables, major main claims, original/reject content, equation/reference/image identities and scope limits |
| Independent final delivery review |38/38 PASS | Reference first-appearance order1–34, current hashes, SI cross-references, remaining comment and claim boundaries |
| Native Word/XML/original preservation |Both PASS | Tracking enabled, unique revision IDs, valid OOXML, logical Reject All restoration; original hashes unchanged |
| Visual layout |75 pages reviewed across clean/tracked views | Main24 clean / 32 tracked;SI3 clean / 16 tracked; no clipping/overlap |

The clean test used a newly created Python3.9.6 venv without inherited system/user site packages, a checkout whose path contains spaces and portable package-root paths. [Isolation evidence](../02_EVIDENCE/reproducibility/clean_environment_isolation.json), exact commands, failed attempts, fixes, dependency locks and successful comparisons are retained in the release evidence. Nine executed computational entry points are SHA-bound to the final stage. The modern offline entry point was separately executed from outside the package working directory after its one placement-dependent root was corrected.

Packaging fixes supplied missing event/calendar inputs, projection metadata, decoded map arrays/basemaps and declared linearmodels/pyshp dependencies. The quality driver previously permitted15 minutes internally although all actual retained gaps were<1 minute (max 0.983333 minute); it now implements the documented<60 second condition, reexecuted with unchanged results. A local archive belonging to a different Nature Cities project was excluded; the actual public repository inventory was used. Historical protocols and defective-baseline negative controls remain clearly dated provenance, not active alternative scientific results. Superseded numbered-SI indexes and incomplete active snapshots are removed only from the new staged package.

This was **not** a new complete raw-provider re-extraction of all city observations. Bulk raw ABI/cloud/SURFRAD bytes are not duplicated in the release; source keys/URLs/hashes and missingness are retained. Optional portable modern native drivers were syntax-checked after I/O-only path changes, not rerun through fresh native downloads in the clean venv. Original executed native/radiometry audit and source-function hashes remain evidence. These limits are explicit in the package README and driver documentation. Passing offline numerical reproduction does not prove every upstream measurement assumption or unique physical cause.

## Local release and remaining authorized steps

The prepared package is version **v2.1.0-r1**, at [the local release directory](../). Its final ZIP, file manifest and SHA256 checksums are generated only after this record and final document checks are copied into the stage. The detached archive verification retained in the author workspace records the resulting ZIP SHA256, byte count, CRC and member-hash checks. The existing public folder names02_EVIDENCE,03_PROTOCOLS,04_CODE,05_CODE,06_SUBMISSION,data,outputs,scripts are preserved. Active corrected content replaces old content in this staged tree; no public content has yet changed.

1. **Author content review now:** review the two tracked Word documents, the modern DQF0–1 station extension, four-table SI and all retained limitations/negative findings. Decide on wording or scientific scope changes. No additional scientific rerun is recommended on the present evidence.
2. **After explicit approval to update GitHub:** synchronize the staged current tree into the verified existing repository while preserving its folder names; inspect the actual deletion/replacement diff; commit, push, tag and publish the approved versioned release with the archive/checksums. These external actions remain authorization-dependent. Do not create an invented release URL/DOI. No obsolete active output should remain beside a new competing version.
3. **Verify public access and update Data Availability:** check the actual published assets and version, then replace future/status language with the real accessible version URL (and DOI only if one is actually issued). Retain native tracking for that Word update; rerender/revalidate and regenerate package hashes because the Word bytes will change.
4. **After author approval of manuscript/SI, draft two separate point-by-point response letters:** reproduce every numbered reviewer comment, acknowledge the concern, explain evidence/change and cite final section/figure/table and regenerated line numbers. State R1-3 as partial and physical/quality/temporal limitations precisely. This step is intentionally **not done now**.
5. **Final submission cross-check:** reconcile every response with actual final text/results, refresh all page/line references, verify captions/equations/references/figure identity and the public release matches the approved document files. Prepare journal-required clean/marked files only following the author's decisions; current suggestions stay unaccepted. Submission itself requires explicit authorization.

The minimum scientifically appropriate next action for remaining experimental gaps is to retain the clear limitations and seek the editor's direction if full urban ground or unique physical attribution is indispensable. A new area-representative urban/ring ground study, L1b/telemetry attribution or unseen-city test would be a separate explicitly scoped project, not an unreported requirement or fabricated completion of this revision.
