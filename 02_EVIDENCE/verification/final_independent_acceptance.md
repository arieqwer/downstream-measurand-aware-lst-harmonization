# Independent repair acceptance — 29 October 2026

**Both newly discovered preprocessing issues pass independent acceptance within the manuscript's affected scientific pipeline.** Local sunset dates are now allocated to their intended intervals, and the fixed polygons are represented by their complete native-grid pixel-centre support. All twelve affected extraction datasets and the downstream calibration/evaluation stages were checked. This statement concerns the two repairs; it does not imply that every scientific validation criterion is satisfied.

No original file, raw provider file, prior fitted model or Word document was changed by this verification. All verifier code and evidence are confined to this directory. A final hash check confirms **299 protected files unchanged, including all five Word files**.

## Independent baseline and negative controls

- The isolated original pipeline replay matches **57 shared CSV/Parquet tables** in shape, columns, missingness and values within 1e−9. Both baseline refitted model files are byte-identical to their original archived files.
- Independent recomputation verifies the six original paired hourly aggregates, the 25-fold model-selection scores and one-SE choices, out-of-fold interval radius, ten sample/scope MSE budgets, representative crossed-bootstrap draws and all reported percentile summaries.
- Negative controls reject the original UTC-date sunset request and the old 655-pixel Los Angeles ring. The checks therefore detect both original defects instead of merely replaying the corrected implementation.

Evidence: [baseline table/model replay](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/baseline_replay_check.json>), [independent baseline analysis checks](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/pipeline_check_baseline.json>), [negative controls](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/negative_control_results.json>).

## Calendar repair — PASS

The verifier independently reconstructs sunset timestamps in a named civil timezone rather than importing the extractor's longitude-offset implementation. Across all twelve repaired datasets, the **832,960 requested city/date/hour rows** satisfy the declared interval membership and nearest-hour acquisition rule. All unique requested city-date sunset timestamps agree exactly with the civil-zone construction (maximum difference **0 seconds**). Pacific, Mountain and Phoenix civil-date controls, plus explicit DST/year-boundary controls, agree with the intended local date.

Each retained output row is matched to an actual archive key for its requested UTC hour; the repair does not substitute another acquisition hour for a missing object. Date/event keys are unique. Missing or geometrically ineligible requests remain visible in the request inventory. The original cohort-selection and missing-data rules are retained.

The verifier checks every reused observation against its original source row, using physical sunset date and exact source key. **732,747 reused rows** retain their original native regional means/counts and scan times exactly. **24,988 rows** were re-extracted for changed spatial support or newly required physical days. Original source Parquet hashes remain unchanged.

Evidence: [all twelve extraction checks](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/repaired_extraction_check_final.json>) and the per-dataset request/provenance manifests under `../extraction/corrected_data/`.

## Complete polygon support — PASS

An independent reference enumerates the entire actual **2500 × 1500 native grid**, then applies polygon membership using Matplotlib paths with holes. A spatial tree is an exact bounding-circle prefilter enclosing each polygon's bounding rectangle; it is not an extraction radius. No projected bounding-window assumption from the generator is used.

The broad inventory covers **2,728 original candidate masks** on the two actual native-grid families. All original radius-35 counts reproduce exactly. The **1,428 masks used by the twelve repaired datasets** match the independent complete-grid row/column arrays exactly, including zero-support cases.

The material repair is Los Angeles's surrounding ring on the west grid: **766 complete pixels replace the inherited 655-pixel subset**. This is corrected in GOES-17 historical calibration/evaluation and GOES-18 historical derivation, 2025 replication and 2026 evaluation. The independent inventory also detects two clipped eastern parent-city rings outside the western manuscript domain; those unrelated parent datasets are preserved rather than silently altered.

Independent CF decoding and complete-polygon aggregation checks on **204 representative regional/tier records**, including changed masks and new boundary scenes across the affected years, agree exactly with the repaired means/counts at the tested floating precision. Full per-file extraction additionally checks the actual native-grid signature against its dataset prototype. This combines full-mask verification with bounded native-value checks; it is not a claim to have independently decoded every unchanged cached file.

Evidence: [complete mask inventory](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/independent_complete_mask_inventory.csv>), [full-grid reference arrays](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/independent_complete_masks.npz>), [native CF checks](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/repaired_native_CF_checks_final.csv>).

## Calibration and evaluation consistency — PASS

The independent reconstruction covers repaired derivation (**13,441 hourly rows**), historical expansion (**9,216**), 2025 original replication (**4,191**), 2025 expansion (**2,948**), 2026 evaluation (**5,716**) and historical 2021 evaluation (**2,602**). All paired daily support, equal-day aggregates and reported component means agree within 1e−9.

Original candidate families, one-SE ordering, calibration periods, geographic/event-block assignment, scoring functions and source-function hashes remain unchanged. The historical offsets and the modern calibration models are refitted on repaired calibration inputs. The selected model **families** remain core `geometry_ridge`, ring `hour_offset`, direct contrast `raw`, and direct transition `raw`; their fitted parameters are updated. The repaired final model SHA-256 is `db6cfc91c55edf840cd857361b5f1c93b6cddcd01474504e5049cb0a82b566bc`.

The repaired model is frozen before its repaired 2026 evaluation pass, and its hash is unchanged afterward. The selection source contains 2025 observations only. Independent checks reproduce all 400 fold scores and four one-SE decisions, the out-of-fold 90% uncertainty radius (**1.5042955308 K**), all ten sample/scope exact MSE budgets, representative direct row-weight bootstrap draws (maximum error **3.18e−14**) and all saved percentile intervals (maximum error **2.23e−16**).

This is a **post hoc correction using the original calibration-only protocol**, after the original 2026 results were already inspected. The original helper's `2026_not_opened` manifest string is a legacy stage identifier, not evidence of a newly untouched prospective test. The 2026 cohort remains a same-city temporal evaluation.

Evidence: [independent repaired pipeline checks](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/pipeline_check_repaired.json>).

## Updated quality, cloud and map analyses — PASS within their stated scope

The independent quality check reconstructs all five scenarios from repaired daily extracts, verifies frozen ridge/offset predictions by explicit algebra, recomputes transitions and MSE budgets, and checks the first ten paired bootstrap draws and every reported percentile interval. The recommended baseline has **30,839 daily pairs, 5,716 hourly rows and 583 transitions**; strict screening retains **883 daily pairs, 215 hourly rows and 21 transitions at three cities**. Sparse strict support remains a scientific limitation, not a preprocessing failure.

The cloud audit verifies **all 32 LST–ACM pairs** by raw hashes, scan start/end, projection and native-coordinate arrays. All **24,000 complete-polygon regional count checks** agree exactly; native CF mean discrepancies are at most **1.87e−5 K**. All thirteen saved metric rows agree within **1.34e−15**, and frozen-model predictions agree with separate ridge/offset algebra. The sample now follows the intended first physical local day of each of the eight intervals; no previous-local-evening relabeling remains. Cloud-screen eligibility is 676 recommended, 588 ACM-clear, 573 one-pixel-buffer and 547 two-pixel-buffer city/date/hour rows. These remain selected scans, not a complete eight-day cloud rerun.

The corrected Phoenix map is independently traced pixel by pixel to its native files, with native grid centres and masks verified. Its physical local date is **1 June 2026** and its actual acquisitions are **2 June UTC**. The shared **240–330 K** scale includes all displayed valid values (minimum about 241.1 K and maximum about 324.2 K). The PNG was independently viewed: timestamps, actual-versus-target hour labels, axes, fixed core/ring outlines and shared scale are readable. The wider scale is a plotting correction; no low-temperature patches or scenes were removed based on their appearance.

Evidence: [quality acceptance](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/auxiliary_quality_acceptance.json>), [cloud acceptance](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/auxiliary_cloud_acceptance.json>), [Phoenix source/array/visual acceptance](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/Phoenix_map_independent_acceptance.json>).

## Scientific gate outcomes must retain their correct labels

Independent transition-row counts verify the reported directional uncertainty results. The formal combined-cohort criteria pass: **524/583 = 89.880% interval coverage**, with **176/186 = 94.624% certified-sign accuracy**. The prespecified coverage band is 85–95%; certified-sign accuracy threshold is 90%.

Descriptive subcohort checks differ. Expansion coverage is **188/238 = 78.992%**, and certified-sign accuracy is **76/86 = 88.372%**; both miss the corresponding numerical criteria. Original-cohort coverage is **336/345 = 97.391%** and certified-sign accuracy **100/100 = 100%**. The formal gate was specified for the combined cohort; subcohort results reveal heterogeneity and should not be described as new prespecified tests. No criterion was retuned to restore a pass.

Evidence: [independently recomputed gate counts and labels](</Users/apple/Downloads/RS revision 1/repair_20261029/verification/uncertainty_gate_acceptance.json>).

## Remaining scientific boundaries

The two newly discovered preprocessing issues are resolved for the affected manuscript pipeline, with new results and models kept separate from the originals. Independent urban core/ring ground validation, causal historical GOES-17 thermal-anomaly attribution, and continuous emissivity/atmospheric perturbation experiments remain distinct previously documented limits. Passing this repair audit does not close those reviewer requirements or establish absolute LST accuracy. Word integration and reviewer-response wording remain author decisions.

Exact verifier commands and exit-zero logs are retained in this directory. Main commands are `check_repaired_extraction.py`, `check_repaired_pipeline.py --mode repaired`, `check_aux_quality.py`, `check_aux_cloud.py`, `check_Phoenix_map_arrays.py`, `check_uncertainty_gate.py`, and `check_protected_inputs.py`, all run with `/usr/bin/python3`. Failed verifier setup attempts are retained alongside successful final records; they did not alter scientific outputs.
