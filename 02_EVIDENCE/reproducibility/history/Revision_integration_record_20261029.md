# Revision integration record for author review

29 October 2026. This is an internal change and decision record, not either reviewer response letter. It supersedes the numerical results and open-task statuses in the earlier `Revision_batch_1_record.md` and earlier recommendation records. Those records are retained as history.

## Current files and scope

- [Manuscript with unaccepted tracked suggestions](../Manuscript%20v1_suggestions.docx)
- [SI with unaccepted tracked suggestions](../supplementary_suggestions.docx)
- Authoritative originals remain `Manuscript v1.docx` and `supplementary.docx` in RS revision 1. Their hashes and the reviewer-comment document hash are unchanged. Earlier suggestion versions were snapshotted before this integration.
- All changes are native Word insertions/deletions, including old/new figures and tables. Track Changes is enabled. No proposed edit was accepted on your behalf. Seven author comments flag decisions/limits.
- Only the consistent repaired results were integrated. The original inputs, earlier reruns and repair evidence remain immutable. No repository push, public deposit, email or journal submission was performed.

## Priority and earlier recommendations

Your 16-comment list covers the reviewers’ numbered concerns. The priority order remains sound: first define consistency/accuracy and validation boundaries, repair the complete affected chain, then evaluate reference uncertainty, covariance/physical diagnostics and cohort transfer; lastly complete structure, figures and format. Two qualifications matter: Reviewer 1 asks for full-process in-situ replication, which the station benchmark only partly addresses; Reviewer 2 permits consistency reframing and bounded diagnostics, which should not be described as causal source attribution.

The seven earlier recommendations were checked individually. Native metadata/quality decoding, strict-DQF common-support sensitivity, a real matched-product map, sampled companion-cloud screening and calendar sensitivity, an independent station benchmark, upstream cohort provenance, and the conditional full repair are completed within their stated scope. The full repair became necessary after two real defects were found. No extra selector/retrieval development, WRF simulation, parent-cohort rebuild or new-city sample was added. The [independent scope audit](records/remaining_tasks_audit.md) retains the original recommendations and their evidence; its pre-integration editorial tasks are now completed as recorded below.

## Integration of the two newly solved issues

1. **Physical local sunset date.** Corrected local-date allocation across calibration and evaluation, then reran all 12 affected study datasets and their dependent processing. Sunset-relative targets are now tied to the physical local sunset date, including UTC acquisitions on the following date. The Phoenix map uses corrected local 1 June 2026 / 2 June UTC. Methods 2.1–2.2, Table 1, Figure 1 chronology, Figure 6 and Note S6 explain the resulting supports and design status.
2. **Complete polygon support.** Replaced extraction bounds that clipped the Los Angeles western ring with full-polygon bounds and double-precision geolocation. The corrected GOES-17/18 ring contains 766 geometric pixels rather than 655. Independently checked all 1,428 masks. Core/ring membership, support, calibration and every downstream result were regenerated consistently. No city cohort was changed to improve results.

Model families, hyperparameters, folds, seeds and selection rules remain the original protocol; coefficients and the residual interval were refitted on corrected calibration data. Because the original 2026 outcomes had already been inspected, the manuscript now calls this **post hoc corrected temporal evaluation**. No 2026 outcome was used to fit or select models. It is not a new untouched prospective test, and it uses the same 75 cities as calibration.

## Results that materially change interpretation

| Quantity | Integrated corrected result | Interpretation |
| --- | --- | --- |
| 2025 calibration | 7,139 hourly rows; 737 transitions; 75 cities | Corrected calibration support |
| 2026 temporal evaluation | 5,716 hourly rows; 583 transitions; same 75 cities | Temporal evidence under the original protocol |
| 2026 core / ring RMSE | 1.748→0.705 / 1.506→0.662 K | 59.7% / 56.1% component improvement |
| 2026 component-derived contrast | 0.8041→0.8053 K; −0.14% RMSE reduction; 95% CI −6.75% to +6.48% | No established contrast improvement |
| 2026 transition | 0.9659→0.9617 K; +0.44% RMSE reduction; +0.88% MSE gain | These percentages are different metrics; their intervals include zero |
| 2021 replication | 2,602 hourly rows; 253 transitions; 69 cities | Corrected historical support |
| 2021 contrast | 0.6385→0.6199 K; +2.9%; 95% CI −4.3% to +9.8% | Small, uncertain improvement |
| Across five evaluation cohorts | Component RMSE improves 29.3–59.7%; contrast ranges from 11.5% improvement to 13.1% deterioration | Component gains do not consistently transfer |
| Hourly covariance penalty | 94.6–114.0% of gross variance-plus-bias gain | Explains the statistical cancellation |
| Fixed 2026 residual half-width | 1.504296 K | Refitted using corrected 2025 data only |
| Pooled directional assessment | Coverage 524/583 = 89.88%; sign agreement 176/186 = 94.62%; 31.90% supported | Both pooled criteria pass |
| Expansion subgroup | Coverage 188/238 = 78.99%; sign agreement 76/86 = 88.37% | **Both fixed criteria fail**; no threshold retuning |
| Original subgroup | Coverage 336/345 = 97.39%; sign agreement 100/100 | Coverage exceeds the specified band |

The final selector remains geometry ridge for core, hour offsets for ring, and raw retention for directly selected contrast and transition. Small results from the component-derived contrast are shown separately from those direct-selected raw actions. Negative results, subgroup failures and large Desert Rock residuals are retained.

## Comment-by-comment changes

The original reviewer wording is reproduced below solely as the source record. It is not adopted as an instruction beyond your revision request. Locations are final proposed section/figure/table anchors. Any page/line references are provisional internal accepted-view PDF locations; final response-letter lines must be regenerated after your content decisions.

### R1-1 — Addressed within the stated diagnostic scope; physical source attribution remains limited

**Original comment**

> 1. It is feasible to use the retrieved land surface temperature of one satellite as a benchmark to calibrate another satellite in the process, but what is the ultimate goal of this paper?  How do you determine what caused the difference between the two?  Is the inversion algorithm consistent with the ancillary data used?  Are the observation angles consistent?

**Where:** Title; Abstract; Introduction; Sections 2.1–2.2, 2.7, 3.5, 4.1 and 4.3; Tables S14, S17–S19; Notes S7–S8.

**What changed:** Clarified the goal as deciding whether correction helps the actual scientific quantity, separately for components, contrasts and transitions. Explained the western-platform reference orientation and retained reference error. Added native-file evidence for the baseline/Enterprise era transition, historical bitmask versus modern categorical quality flags, sampled algorithm/parameter families and ancillary templates. Reported unequal viewing zenith angles (2026 reference 43.74–59.68°, source 52.61–72.25°), geometry strata and quality/cloud comparisons.

**Boundary / recommendation:** Matching metadata families do not establish identical numerical emissivity or atmospheric inputs. Geometry strata contain different cities and do not isolate a causal angular effect. No new radiance retrieval is recommended.

**Provisional locators:** Manuscript p. 3, line 97–103 (P33); Manuscript p. 6–7, line 186–196 (P114); Manuscript p. 12, line 414 (P159); SI, paragraph anchor P1310.

### R1-2 — Addressed editorially

**Original comment**

> 2. The second part of the overall logic chaos, please reorganize

**Where:** Section 2.1–2.7 and the methods roadmap.

**What changed:** Organized methods in dependency order: design/cohorts → satellite pairing and spatial/temporal support → measurands and model selection → MSE decisions → transfer regimes → uncertainty → native sensitivities and independent station benchmark. Added the Section 2.7 methods destination for the new analyses, linked to Results 3.5. Reduced repeated design qualifications and maintained figure/table connections.

**Boundary / recommendation:** Required new diagnostic material increases the total length; this revision claims improved organization and less repetition, not a shorter total manuscript.

**Provisional locators:** Manuscript, paragraph anchor P30; Manuscript p. 12, line 414 (P159).

### R1-3 — Partially addressed; principal remaining scientific gap

**Original comment**

> 3. It is suggested to reproduce the whole process of this paper based on the in-situ data, cross-validate the retrieved LST by different satellites, and clarify the reasons that may lead to LST inconsistency.

**Where:** Sections 2.7, 3.5, 4.3 and Conclusions; Tables S20–S21; Note S9; Data S18.

**What changed:** Added an independent SURFRAD raw-product benchmark at Desert Rock, Fort Peck and Table Mountain. There are 413 common GOES-16/17 station-time pairs on 31 local dates (157/145/111 by site). Pooled RMSE is 4.678/4.094 K and bias −3.249/−3.110 K. Reported each site, all retained missingness, radiometric-temperature calculation, reflected downwelling flux, QC and time support. Added assumed-emissivity ±0.01, uniform emissivity, radiometry, nearest-minute and 3×3-neighborhood sensitivities. A separate 25-pair station cooling comparison is labeled station scale.

**Boundary / recommendation:** This does not reproduce the city-trained correction plus urban core–ring contrast and transition against matched ground observations. Recommend retaining the benchmark and candid full-workflow limitation. Full completion requires area-representative urban/ring radiometry and additional time or an extension. Do not apply city corrections to unrelated station pixels or construct an urban contrast from distant stations.

**Provisional locators:** Manuscript p. 12, line 414 (P159); Manuscript p. 17, line 569 (P226); Manuscript p. 20, line 682–691 (P248); SI p. 19 (P1459); SI p. 20 (P1462); SI p. 20 (P1495).

### R1-4 — Addressed

**Original comment**

> 4. For remote sensing papers, I can't understand the full text without the spatial distribution LST map.

**Where:** Figure 6 and caption; Results 3.5; Note S8.

**What changed:** Inserted actual GOES-18/19 native LST spatial fields around Phoenix for corrected local 1 June 2026 (2 June UTC), at target sunset-relative bins −3/+4. The figure gives actual acquisition times/offsets, coordinates and complete core/ring outlines. A common 240–330 K color scale retains all displayed valid pixels, quality gaps and cold patches. The caption specifies screening, nominal resolution and distinct native footprints; no inter-platform interpolation is implied. The map is illustrative spatial evidence, separately from Figure 1 geography.

**Boundary / recommendation:** It is not a cloud-free truth scene. The scene was not reselected to hide cold patches or missingness. Source scripts and exact figure bytes are retained.

**Provisional locators:** Manuscript p. 17, line 569 (P226); Manuscript p. 19, line 594–600 (P231).

### R2-M1 — Addressed by consistency framing plus bounded independent evidence

**Original comment**

> The study is exclusively an inter-platform consistency assessment with an arbitrarily chosen reference platform; no absolute validation (e.g., SURFRAD or other surface radiometry) is performed, yet the title uses "Validation," and the reference platform's own error structure — in particular the GOES-17 ABI thermal anomaly — is never discussed..

**Where:** Title; Abstract; Sections 2.1–2.2, 2.7, 3.5 and 4.3; Note S9.

**What changed:** Replaced accuracy implications with inter-platform consistency assessment throughout the main claim. Explained why GOES-17/18 are the designated western reference scales and why their own errors remain. Added the independent historical station benchmark and explicit GOES-17 thermal/availability limits. The reference is never treated as error-free or proven more accurate.

**Boundary / recommendation:** Absolute accuracy of the full urban workflow and universal superiority of the reference platform are not demonstrated.

**Provisional locators:** Manuscript p. 1 (P1); Manuscript p. 1, line 22–38 (P22); Manuscript p. 3, line 97–103 (P33); Manuscript p. 20, line 682–691 (P248).

### R2-M2 — Addressed editorially and bibliographically

**Original comment**

> Methodological novelty is limited — the MSE decomposition is an accounting identity (acknowledged by the authors), the "measurand-aware selector" is standard cross-validated model selection with a one-standard-error rule.

**Where:** Introduction; Sections 2.3–2.4 and 4.1–4.2; Conclusions; reference 26.

**What changed:** Attributed the MSE identity, cross-validation and one-standard-error rule to established mathematics and statistics. Repositioned the contribution as their integrated measurement-level application and evaluation across GOES replacements: component correction, derived-measurand assessment, direct correction versus raw retention, and directional abstention. Added the standard model-selection reference and retained covariance/metrology sources.

**Boundary / recommendation:** No new decomposition or selector is claimed. The linear generalization is identified as algebra; nonlinear applications remain proposals.

**Provisional locators:** Manuscript p. 2, line 81–90 (P29); Manuscript p. 8, line 238 (P119); Manuscript p. 10, line 314 (P133); Manuscript p. 19, line 602 (P233).

### R2-M3 — Addressed through provenance and editorial revision; public delivery pending

**Original comment**

> The writing is excessively long and defensive ("prespecified/frozen" appears more than 19 times), the cohort provenance ("pre-existing higher/lower-vegetation-support cohorts") is uncited, and readability suffers badly.

**Where:** Highlights; Sections 2.1, 4.3; Table S1; Note S1; Data S20 and archive provenance.

**What changed:** Reduced repeated prespecified/frozen wording while retaining necessary calibration boundaries. Traced the 5,541-city parent collection, inherited exclusions, median split of daytime vegetation-observation support in the 10–20-km ring, western 51/43 candidate pools and retained 44/31 groups. Explicitly distinguished observation support from vegetation-cover fraction. Archived 12 upstream cohort sources with hashes and the selection evidence, rather than inventing an external publication for project-specific cohorts.

**Boundary / recommendation:** The locally assembled archive still needs a public release and clean-environment/path check. New diagnostics add length; overall word-count reduction is not claimed.

**Provisional locators:** Manuscript p. 3, line 104–114 (P34); SI p. 15 (P1043); SI, paragraph anchor P950.

### R2-M4 — Consistency reclassification completed; LHP sensitivity bounded

**Original comment**

> 4. Validation semantics and the reference platform — no absolute reference, and the GOES-17 ABI thermal anomaly is not discussed.It should be add some contents in the revised manuscript: i.e., (a) discuss the potential impact of the GOES-17 LHP anomaly on the reference scale and the hour-offset corrections, with a sensitivity statement; (b) reposition the study throughout (title, abstract, text) as inter-platform consistency validation, or add validation against an independent surface reference.

**Where:** Title; Abstract; Sections 2.2, 2.7, 4.3; Table S16; Notes S4 and S7.

**What changed:** Described the loop-heat-pipe anomaly, uncertain reference scale, documented July 2021 operational events, and how fitted hour offsets can absorb reference bias, source bias and sampling effects. Recomputed the fixed-offset June-only exclusion after calendar repair: 1,330 hourly rows, contrast RMSE 0.6255→0.6073 K and net MSE gain 0.0224 K², compared with 0.0234 K² for all windows. Added native missing-object/metadata evidence. Adopted the reviewer’s consistency-framing option.

**Boundary / recommendation:** Calendar exclusion does not isolate LHP effects; unavailable thermal-state/mitigation flags do not imply anomaly-free observations. A causal telemetry/L1b attribution experiment is not completed and is not recommended within the present scope absent an editor requirement.

**Provisional locators:** Manuscript p. 20–21, line 692–700 (P249); SI p. 17 (P1273); SI p. 17 (P1275).

### R2-M5 — Addressed through design and inference corrections

**Original comment**

> 5. Sampling design limits generalization, and the "prospective holdout" is less independent than presented, i.e., the 75 cities in the 2026 holdout are identical to those in the 2025 calibration — the final prospective test is temporal only and provides no evidence about spatial generalization.

**Where:** Abstract; Section 2.1; Figure 1 chronology/caption; Table 1; Sections 3.3, 4.2–4.3; Note S6.

**What changed:** Explicitly stated that 2025 calibration and 2026 evaluation use the same 75 cities. Updated the chronology graphic through its traced generating script. Distinguished earlier spatial/platform tests from final-workflow temporal evaluation. Because preprocessing was repaired after original 2026 results were inspected, described the new result as post hoc corrected temporal evaluation under the original protocol; only 2025 data fitted/selected the revised models.

**Boundary / recommendation:** The corrected 2026 data cannot be called untouched prospective evidence. Spatial generalization of the final 2025-selected workflow to unseen cities remains untested. No extra city sample is necessary to make the present claims accurate.

**Provisional locators:** Manuscript p. 3, line 115–123 (P35); Manuscript p. 6, line 166–182 (P43); Manuscript p. 14, line 508 (P177); Manuscript p. 20, line 650 (P241); SI p. 17 (P1307).

### R2-M6 — Quantitative diagnostic response integrated; causal attribution remains bounded

**Original comment**

> 6. The manuscript currently lacks physical mechanism diagnostics and sensitivity analyses, which require supplementation. Specifically, (1) the current study does not explain why harmonization reduces the core–ring residual correlation from 0.885 to 0.554. As demonstrated in Table S8, core and ring exhibit significantly distinct hour offsets before sunset (3.68 K versus 3.06 K when h = −3), which indicates that the underlying mechanism is that differential time-varying correction eliminates the shared error structure. However, the manuscript only notes that this observation "does not identify causal mechanisms" without further discussion, and does not carry out component decomposition analysis across dimensions including hour, view zenith, DQF tier, cloud screening, and emissivity/atmospheric inputs. Furthermore, the typical UHI contrast magnitude (~2–5 K) is not compared with the cross-platform discrepancies (~0.6–0.9 K), making it difficult for readers to assess its practical impact. The authors should add these diagnostics or at least quantify the associated concerns.

**Where:** Sections 2.4, 2.7, 3.2, 3.4–3.5, 4.1 and 4.3; Tables S13–S21; Notes S2–S5 and S7–S9.

**What changed:** Recomputed historical residual correlation (0.885930→0.535019), replacing the reviewer’s quoted old corrected value. Showed why hour-specific additive corrections leave the weighted within-hour covariance contribution unchanged (0.208521 K²) while between-hour covariance falls from 1.228250 to 0.006393 K². Updated hour offsets, including core–ring offset difference 0.5884 K at h=−3. Added hour and VZA strata; native DQF/quality reasons; strict-quality common-support and paired sensitivity; eight sampled days of matched cloud masks and dilations; ancillary availability and ground-emissivity sensitivity. Compared actual median absolute reference contrasts (1.670/1.818 K in 2021/2026) with raw discrepancy RMSE (0.638/0.804 K), aggregate scale ratios 38.2%/44.2%.

**Boundary / recommendation:** Strict screening retains only 3 cities/215 hourly rows/21 transitions. Cloud evidence is scan-level on eight sampled days, not full interval/transition validation. Ground-emissivity perturbation is not ABI retrieval-input perturbation. Geometry strata and metadata do not uniquely identify physical causes. Preserve uncertainty crossing zero and the expansion gate failures; do not tune them away.

**Provisional locators:** Manuscript p. 13, line 467 (P170); Manuscript p. 15, line 531 (P219); Manuscript p. 17, line 569 (P226); Manuscript p. 19, line 602 (P233); SI p. 15 (P1045); SI p. 18 (P1350).

### R2-m1 — Addressed

**Original comment**

> Equations are unnumbered throughout; please number them per journal style.

**Where:** Section 2 display equations (1)–(12).

**What changed:** Retained 12 numbered main display equations, editable original math objects and corresponding references. Checked numbering after all additions; new station radiometry is defined in prose without an unnumbered main display.

**Boundary / recommendation:** Refresh any cross-references after author edits.

**Provisional locators:** Manuscript p. 8, line 238 (P119); Manuscript p. 10, line 314 (P133).

### R2-m2 — Addressed

**Original comment**

> Does Highlightshave such a large number of words?

**Where:** Highlights.

**What changed:** Retained the journal-style two questions with two concise bullets under each. Updated only the repaired global component/contrast ranges and covariance fraction, while preserving the central implication and processing decisions.

**Boundary / recommendation:** No unrelated 85-character Highlights rule was imposed. The four bullets are final proposed text for author review.

**Provisional locators:** Manuscript, paragraph anchor P14; Manuscript p. 1, line 12–13 (P16); Manuscript p. 1, line 14–15 (P17).

### R2-m3 — Addressed

**Original comment**

> Undefined term at first use: "95% crossed-bootstrap interval" appears in the abstract without defining "crossed" (city-by-interval resampling); define it briefly or standardize on "crossed city–interval bootstrap" (the two phrasings are currently used interchangeably).

**Where:** Abstract; Section 2.6; figure/table captions; Tables S5–S6 and Note S9.

**What changed:** Defined crossed city–interval bootstrap at first Abstract use as independent resampling of cities and intervals, and used that term consistently. Distinguishes observed estimates, bootstrap means and 95% intervals. The separate station analysis uses crossed station–date draws (and a station–interval sensitivity), rather than city–interval terminology.

**Boundary / recommendation:** Final response letters must distinguish RMSE-reduction percentages from MSE-gain percentages and their separately transformed intervals.

**Provisional locators:** Manuscript p. 1, line 22–38 (P22); Manuscript p. 11, line 385 (P154); SI, paragraph anchor P389; SI, paragraph anchor P477; SI p. 19 (P1459).

### R2-m4 — Addressed; supplied revised basemap retained and clarified

**Original comment**

> Figure 1(b): the map shows only points and the 100°W boundary, with no coastline or state boundaries, making spatial orientation difficult; please add a basic geographic basemap.

**Where:** Figure 1(b) and caption.

**What changed:** Verified the supplied authoritative Figure 1 already contains land/water, coastline, national/state/province boundaries, north arrow and scale bar. Preserved these geographic elements in the traced regeneration; clarified city symbols and the predefined 100°W cutoff in the caption. Changed chronology labels for R2-M5 through source code.

**Boundary / recommendation:** The eventual response should describe the current figure without speculating about which image version the reviewer saw.

**Provisional locators:** Manuscript p. 6, line 166–182 (P43).

### R2-m5 — Addressed through format and targeted metadata checks

**Original comment**

> Please verifythereferences, which have inconsistent formatting.

**Where:** References; all main numeric citations; explicit SI reference pointers.

**What changed:** Retained the earlier visible-format normalization of original references, added six verified references to the prior 28-entry suggested version, and globally reordered all 34 by first appearance. Verified new authors/year/title/volume/pages-or-article-ID/DOI against primary or publisher-deposited metadata. Matched DOI/URL hyperlink styling, and updated seven explicit SI references using the same identity map.

**Boundary / recommendation:** This is a full visible-format and citation-order audit plus targeted metadata verification, not a claim that every unchanged old reference was independently revalidated. Final clean-page lines must be refreshed after acceptance.

**Provisional locators:** Manuscript, paragraph anchor P286.

### R2-m6 — Addressed

**Original comment**

> "11,132-m scale" (§2.1): ERA5-Land is ~0.1° (≈11.1 km); "~11.1 km (0.1°)" would be cleaner.

**Where:** Section 2.1.

**What changed:** Replaced the isolated 11,132-m presentation with ~11.1 km (11,132 m in Earth Engine) nominal reduction scale on the distributed 0.1° grid. Distinguishes the reduction parameter from native resolution and geographic cell dimensions.

**Boundary / recommendation:** No ERA5-Land input rerun is required by this wording change.

**Provisional locators:** Manuscript p. 3–4, line 132–149 (P37).

## Remaining issues and decisions

1. **Full urban ground validation remains incomplete.** Recommended route: submit the completed station benchmark and explicitly limited urban consistency claims. The response to R1-3 must acknowledge that the complete urban workflow was not reproduced against ground truth. If full completion is essential to you or required by the editor, seek an extension and obtain matched area-representative urban core/ring radiometry. An additional distant-station or modern-satellite rerun alone does not close that gap.
2. **Causal LHP and continuous ABI input perturbations remain unavailable.** The calendar, native metadata, hour, geometry, quality and cloud evidence support a bounded quantitative discussion. They do not identify a unique physical cause. Recommend retaining that limit rather than starting a new L1b/telemetry/retrieval project for this round. Ground-emissivity scenarios must not be relabeled as ABI retrieval-input tests.
3. **Final-workflow spatial generalization remains untested.** The revised manuscript states this. Recommend retaining the temporal scope; no extra new-city run is needed to correct the claims. A future independently specified external evaluation can extend the evidence.
4. **Public corrected release remains pending.** The local Supplementary_Data package contains 438 manifested files (about 101 MB), all hashed and checked. Choose/confirm the existing repository release and whether to add an archival DOI, review which upstream project files can be public, configure the host-specific script paths, and run the documented package workflow in a clean environment before release. Then replace the future-tense Data Availability wording with actual versioned links. No public release is claimed here.
5. **Author/coauthor acceptance is still needed.** Review the post hoc qualification, small/uncertain downstream gains, both expansion failures, station support limits and Desert Rock findings. These are supported outcomes to approve for reporting, not quantities to adjust until favorable. The manuscript and SI have anchored author comments at the main decision points.

No additional full scientific rerun is indicated by the completed checks. Do not retune the fixed interval to rescue the expansion cohort, discard Desert Rock for large errors, or repeatedly refit/retest inspected data as a new prospective experiment. A new analysis should follow a concrete new requirement or discrepancy.

## Exact edit records and verification

- [Final comment coverage JSON](records/reviewer_coverage_final.json) and [TSV](records/reviewer_coverage_final.tsv) retain all 16 verbatim comments, status, locations, changes, limits and operation mappings.
- [Final integration ledger JSON](records/final_integration_change_ledger.json) and [TSV](records/final_integration_change_ledger.tsv) retain exact before/after text, reviewer tags and source paths for this integration. The prior batch ledger remains at `../revision_work/records/change_ledger.json`; earlier proposals superseded numerically by this integration are historical, not alternate final results.
- [Paragraph location index](records/final_paragraph_locations.json) and [rendered line index](records/rendered_line_index_final.json) permit rebuilding response-letter locations. Short repeated table values are deliberately not assigned misleading unique line locations.
- [Structural checks](records/structural_validation.json): both Word packages pass ZIP/core schema checks; tracking is enabled; IDs are unique; all comments are anchored; Reject All reconstructs original content; original editable math and original media are retained.
- [Independent manuscript audit](records/independent_main_science_audit.md): **265/265 checks pass**, using accepted Word content against source results, including all six embedded figure bytes and scope limitations.
- [Independent SI audit](records/independent_si_science_audit.json): **867 numeric/boolean cell comparisons pass**, plus table dictionaries, notes, source-package hashes and an old-count negative control. There are 21 numbered tables (22 physical tables because S12 continues), nine Notes and 20 numbered Data entries.
- [Citation audit](records/references/final_refresh.log): 34 references in first-appearance order, six new reference identities checked, no duplicate DOI, seven SI reference pointers consistent. Earlier unchanged reference metadata were not all independently revalidated.
- [Final visual QA](records/final_visual_QA.md): accepted preview manuscript 24 pages/SI 20 pages; tracked preview 33/20 pages. Every page was inspected or matched byte-for-byte to an inspected page. Formatting defects found during checking were repaired; final documents pass.
- [Local data package validation](records/supplementary_package_final_check.json) and `Supplementary_Data/02_EVIDENCE/si_tables/validation_report.json`: provenance copies/indexes and manifested file hashes match. This is local package integrity, not proof of public access or one-command portability.

Figure provenance is retained: Figure 1 was regenerated from the traced workflow/domain/chronology source with corrected labels; Figures 2–5 come from the repaired analysis scripts; Figure 6 comes from the corrected native-map script. Original figure bytes remain in tracked deletions. Exact commands, unsuccessful intermediate checks and repairs are retained in `scripts/` and `records/`, so final PASS claims do not erase their history.

## Detailed next steps to finish the full revision round

1. **Review these two tracked Word files and this record.** Resolve the seven anchored author comments and approve the scientific scope, particularly full urban ground validation and post hoc temporal status. Coauthors review negative/subgroup results. The present edits remain unaccepted until you decide.
2. **Make only evidence-driven final changes.** If you retain the recommended bounded scope, proceed directly to editorial completion. If you require full urban ground validation or the editor explicitly requires it, define the matched observation design and request time before promising a result. No routine recomputation is pending.
3. **Finish reproducibility delivery.** Choose the versioned repository/archive destination, review releasable upstream sources, remove/configure local machine path assumptions, document environment and commands, smoke-test from a clean checkout, verify hashes and publish only after your authorization. Update the manuscript/SI links to the actual release and DOI if obtained. Retain corrected versus original version labels.
4. **Freeze the revised scientific content.** Resolve suggestions with the authors, update dependent cross-references and export a definitive line-numbered clean manuscript and matching SI. Keep a marked version. Check figure source files, captions, units, equations, citation numbers, sample denominators and archive inventories once more after any author changes.
5. **Draft the two reviewer response documents after content approval.** Use conventional point-by-point formatting: reproduce each original numbered comment verbatim, then give a courteous direct response, describe the actual change and cite revised sections and definitive line numbers (SI table/note/page where suitable). Keep Reviewer 1 and Reviewer 2 separate. Explain partial completion and limits directly. These response letters have not been drafted, as requested.
6. **Cross-check the complete submission set.** Match every response claim to actual accepted text/figures, ensure no unsupported claim of independent urban accuracy or untouched prospective validation, and ensure Data Availability points to accessible corrected files. Confirm the journal’s requested clean/marked formats, figure quality, supplementary filenames, title/author metadata, funding, declarations and author approvals.
7. **Submit after final author approval.** Retain time for portal/PDF proof inspection and any last upload corrections. The remaining work is mainly author decisions, public-release preparation, response writing and submission QA; a fresh full pipeline run is not the critical path.

No official reviewer response letters or journal submission have been produced in this step.
