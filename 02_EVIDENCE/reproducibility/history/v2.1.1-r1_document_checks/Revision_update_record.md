# R1 revision update for author review

31 October 2026. This record documents the four author suggestions and their integration into the current tracked manuscript/SI. It supersedes the word counts, four-table SI inventory, page counts and local candidate version in the preceding completion record. Earlier scientific findings and limitations remain valid. This is an internal change/evidence log, not either reviewer response letter.

## Current files and overall result

- [Current manuscript with native unaccepted Track Changes](Manuscript%20v1_suggestions.docx)
- [Current SI with native unaccepted Track Changes](supplementary_suggestions.docx)
- [Preceding full reviewer-coverage and scientific completion record](../02_EVIDENCE/reproducibility/history/v2.1.0-r1_document_checks/Revision_completion_record_20261030.md)
- [Exact before/after change ledger](../02_EVIDENCE/reproducibility/document_checks/change_ledger.json)
- [Updated disposition of all 16 reviewer comments](../02_EVIDENCE/reproducibility/document_checks/reviewer_coverage_final.tsv)

All four suggestions are scientifically appropriate. Changes1–3 are integrated; Change 4 is retained as an evidence/reporting boundary and a plan for the later response, with no additional extensive ground study. No response letter was drafted, no existing suggestion accepted, and no external publication/submission performed. The original manuscript, original SI, original reviewer document and the pre-pass suggestions are preserved and SHA-checked in snapshots.

## Change 1 explicit unfavorable transition sensitivity

**Where:** Section 3.5, first paragraph; accepted-view preview p15 lines492–497 begins the sample restriction and new results. Its conditional/bootstrap qualification continues on p16. SI S2 remains unchanged onSI p2.

**New sentence:** “On the same restricted support, component correction increased transition-contrast RMSE from 0.961 to 0.992 K under recommended screening and from 0.816 to 0.840 K under strict DQF-0 screening.” The following comparison is now explicitly labelled an **hourly** corrected RMSE difference, to distinguish it from these transition results.

The exact values were independently rebuilt from the common-support hourly data: recommended 0.9611786586958676→0.9915247947503749K and strict 0.8159860343363704→0.8399358645768968K. Both use21 transitions across Tucson, South Valley and Albuquerque, with eight intervals. The paragraph already gives those counts and the geographically/geometry-dependent selection, and retains the qualification that the conditional comparison cannot establish robustness for all75 cities.

These are transitions derived after component correction. They are separate from the final selector's raw-retention action for the direct transition. No thresholds, corrections, data or model decisions changed. This strengthens R2-M6 without interpreting a sparse sensitivity as population-wide validation.

## Change 2 manuscript shorter than original

| Counting basis | Original supplied manuscript | Before this pass | Current proposal |
| --- | ---: | ---: | ---: |
| Paragraph text including references, excluding table cells |8,762|10,202|**8,518**|
| Including table-cell paragraphs |9,105|10,556|**8,872**|

The manuscript is244 words shorter than the original by the requested method and233 words shorter with table text included. It is1,684 words shorter than the preceding proposal (16.5%). Counts use the same whitespace split of accepted Word paragraph text, including front matter, captions and references; native equation tokens are treated consistently. They are reproducible extraction counts, not a claim about Word's potentially different native tokenization. [The count record](../02_EVIDENCE/reproducibility/document_checks/word_count_comparison.json) includes the exact rule.

The500–900word suggestion could not itself satisfy the author's stronger below-original requirement: the preceding proposal exceeded the original by1,440 words before adding the strict-transition sentence. A larger targeted reduction was therefore necessary. Cuts remove duplicate motivation, repeated design qualifications, verbose census/selection explanations, repeated interpretation and generic extensions. They do not move required method descriptions back into SI.

| Manuscript area | Paragraph edits | Net words removed |
| --- | ---: | ---: |
| Introduction | 4 | 189 |
| Methods | 17 | 826 |
| Results and captions | 15 | 301 |
| Discussion and Conclusions | 10 | 365 |
| Back matter | 2 | 3 |

The edited manuscript has22 clean-preview pages, compared with24 before this pass. Figure bytes, reference entries and the12 numbered display equations are unchanged. All 18 native math objects, including the embedded temperature symbol and√15/√25, remain editable and correctly positioned. The formatting-sensitive general-linear paragraph was left unchanged rather than risking its superscripts.

Independent semantic review checked all operative cohort/census rules, grid/physical-local-date and pixel support, primary quality rules, blocked folds, one-standard-error rule, higher empirical residual quantile, fixed directional criteria and station timing/radiometry. New station methods/results, quantitative covariance partition, observed contrast scales, negative 2026/subgroup findings and explicit scope limits remain. The sole removed citation instance is a repeated citation3; all 34bibliographic identities and their first-appearance order1–34 are preserved.

## Change 3 compact inspectable diagnostic evidence

**Where:** NewSI Table S5 onSI p4, cited at the end of Results3.4 (accepted main previewp14lines475–476) and in the updated Supplementary Materials inventory. The SI now has **five tables, zero Notes and four clean pages**. S1–S4 captions and data cells are unchanged. A marked view displays17 pages because original deletions remain visible and unaccepted.

S5uses23 rows and six columns: the2021 pooled result, allten 2021hour bins, allten 2026hour bins and both populated2026 GOES-18reference-VZA strata. Each row gives observation/city counts, raw/corrected contrast RMSE, gross variance-plus-bias gain, covariance-loss penalty and net MSE gain. All eight unfavorable modern-hour gains and the unfavorable50–60° VZA stratum remain visible. Showing both years avoids presenting only the historical hours that improved. The entire table/caption fits on one portrait page.

The caption defines support, units, angle-bin boundaries and budget signs; it distinguishes fixed historical hour-shift invariance from pooled between-hour covariance and states that VZA groups contain different cities and do not isolate angular causes. Full-precision separate variance/bias terms remain in the numeric companion and complete source tables.

[The direct diagnostic index](../REVIEWER_DIAGNOSTICS.md) gives21 verified local filelinks covering hours, covariance partition, differential offsets, reference/source geometry, DQF/common support and uncertainty, sampled cloud screening, native ancillary/PQI metadata, ground-reference scenarios, GOES-17 calendar sensitivity and actual contrast scales. It provides exact filenames and fields rather than requiring a reviewer to search the repository. Public version-specific links will be available only after an authorized release; none was invented.

## Change 4 R1-3 remains a meaningful partial response

The current manuscript preserves413 historical GOES-16/17pairs and173/109 modern GOES-18/19pairs, all three sites, uncertainty and sensitivities. It retains the first-local-day support, distinct modern DQF0–1tier, all 282 modern GOES-19pixels being DQF1, zero joint strict DQF0 pairs and the absence of cross-era ranking evidence.

The three points for later author-approved response work are recorded explicitly:

1. **Independent evidence obtained:** station radiometry evaluates each raw satellite product on matched station/time support. Methods 2.7andResults 3.5report what was measured and how it was matched.
2. **Why full workflow validation remains incomplete:** a point station and directional satellite pixel do not provide matched area-representative urban-core and10–20-km-ring observations; they cannot ground-validate the full spatially aggregated contrast/transition chain or city-trained correction.
3. **What the primary conclusion supports:** consistency against a designated satellite reference at the target measurand, with reference error retained; it does not establish absolute accuracy of the complete urban workflow. Introduction, Methods 2.1/2.4, Results 3.5, Discussion 4.3andConclusions preserve this scope.

R1-3 is **partially addressed**, not fully satisfied. No extensive new ground validation is recommended on the existing evidence. Additional area-representative observations would be required if the editor makes full workflow ground validation indispensable. These are reporting decisions and limitations, not a drafted response letter.

## Exact changes and tests

The ledger records48 targeted text edits, one native paragraph-format edit and two SI operations. Paragraph indices below refer to the pre-pass accepted Word map and remain stable for this edit set. The full before/after text and sources are in the JSON ledger.

| Change ID | Baseline paragraph | Reviewer concern | Reason |
| --- | ---: | --- | --- |
| CONC-M-001 | 26 | R2-M3 | Remove duplicated examples of radiometric/spectral/geometry harmonization while preserving the introduction and first citation appearances. |
| CONC-M-002 | 27 | R2-M3 | Combine repeated statements of covariance propagation and downstream validation motivation; retain every cited identity and their order. |
| CONC-M-003 | 28 | R2-M3 | Condense instrument/product motivation while retaining retrieval dependencies, platform timing/status, physical contrast meaning and cited sources. |
| CONC-M-004 | 29 | R2-M3 | State the objective, established methods, contribution and consistency scope once without repeating the full measurement chain. |
| CONC-M-005 | 31 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-006 | 33 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-007 | 34 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-008 | 36 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-009 | 37 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-010 | 38 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-011 | 42 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-012 | 115 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-013 | 116 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-014 | 117 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-015 | 118 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-016 | 119 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-017 | 129 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-018 | 130 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-019 | 131 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-020 | 151 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-021 | 161 | R2-M3 | Remove repeated design explanations, duplicate table/figure detail and verbose syntax while retaining operative methods and scope. |
| CONC-M-022 | 167 | R2-M3 | Remove redundant recurrence/design statement already given by the cohort comparisons; preserve numerical range and exact evidence filename. |
| CONC-M-023 | 170 | R2-M3 | Shorten caption by removing repeated expanded acronyms and descriptions of visible zero lines; retain every model/calibration-to-evaluation mapping and signed-budget convention. |
| CONC-M-024 | 171 | R2-M3 | Remove duplicated global contrast range while preserving all five cohort outcomes and the uncertain2026 interval. |
| CONC-M-025 | 172 | R2-M3 | Remove rhetorical opener and redundant terminology while retaining all signed transition gains and cohort mapping. |
| CONC-M-026 | 175 | R2-M3 | Avoid repeating the variance/covariance interpretation immediately after the complete numerical budget. |
| CONC-M-027 | 176 | R2-M3 | Condense the deterministic stress-test interpretation; retain bounded nature and all exhaustive-grid counts. |
| CONC-M-028 | 177 | R2-M3 | Remove repeated gross-gain/covariance definitions while preserving every empirical cohort position and sign reconstruction. |
| CONC-M-029 | 181 | R2-M3 | Combine repeated selected-action and downstream-uncertainty statements; preserve model identities, metrics, intervals and calibration-only decisions. |
| CONC-M-030 | 182 | R2-M3 | Remove repeated rationale for retaining raw, already stated in Methods and the preceding Results paragraph. |
| CONC-M-031 | 183 | R2-M3 | Tighten the directional Results while retaining all denominators, support percentages, both expansion failures and original overcoverage. |
| CONC-M-032 | 223 | R2-M3 | Remove repetition of the historical design motivation; retain component/contrast point estimates and intervals. |
| CONC-M-033 | 225 | R2-M3, R2-M6 | Remove repeated explanation of hour-dependent mean shifts while preserving the differential-offset numbers, within-hour result and model-specific invariance boundary. |
| CONC-M-034 | 226 | R2-M3 | Shorten interval influence/transition reporting without deleting the uncertain unfavorable transition result. |
| CONC-M-035 | 228 | R2-M3 | Condense caption and make original-cohort overcoverage explicit beside both expansion failures; preserve supports, resampling and post hoc limits. |
| CONC-M-036 | 230 | R2-M6 | Make both unfavorable common-support transition results explicit; retain21-transition/three-city conditional scope and distinguish hourly comparison. |
| CONC-M-037 | 238 | R2-M3 | Remove repeated full interpretation of the already reported MSE/covariance decomposition while retaining model-specific statistical mechanism and separate transition accounting. |
| CONC-M-038 | 241 | R2-M3 | Consolidate novelty positioning and remove repeated definitions while preserving all citations and established-method attribution. |
| CONC-M-039 | 242 | R2-M3 | Remove numerical repetition already present in Results/Table2; preserve calibration decision, temporal evidence and practical inference. |
| CONC-M-040 | 243 | R2-M3 | Condense repeated identity-candidate/raw-retention rationale into its practical implication. |
| CONC-M-041 | 244 | R2-M3 | Remove duplicated31.9%/94.6% values retained in Abstract/Results/Table2/SI and preserve citation support and every subgroup failure. |
| CONC-M-042 | 246 | R2-M3 | State each transfer regime once; retain same-city/post hoc and unseen-city limits without repeating design chronology in full. |
| CONC-M-043 | 247 | R2-M3 | Remove duplicated subtraction/covariance explanation and keep a clearly prospective, untested extension. |
| CONC-M-044 | 250 | R2-M3 | Remove repeated general conclusion; retain nonlinear boundary, citation and prospective nature. |
| CONC-M-045 | 256 | R2-M3 | Condense conclusion by removing repeated workflow framing; preserve headline ranges, covariance finding and incomplete ground validation. |
| CONC-M-046 | 257 | R2-M3 | Remove duplicated operational explanation while retaining negative directional outcome, empirical bounds and future-validation requirement. |
| CONC-M-047 | 258 | R2-M3, R2-M6 | Update compact five-table SI map; supporting evidence remains in the indexed versioned package. |
| CONC-M-048 | 261 | R2-M3 | Bind revised documents to a new local release candidate; publication remains pending. |
| CONC-M-FORMAT | 184 | R2-M3 | Repair the orphaned Table 2 caption found in full rendered-page QA; native paragraph-format change remains unaccepted. |
| CONC-SI-001 |  | R2-M6, R2-M3 | Update concise inventory for one compact principal-diagnostics table. |
| CONC-SI-002 |  | R2-M6 | Expose principal hour and VZA evidence with sample sizes and signed MSE budgets in one table. |

| Executed check | Outcome | Evidence |
| --- | --- | --- |
| Independent diagnostic/transition source reconstruction |180/180 PASS|proposals/diagnostic_access_verification.json|
| Additional modern-hour reconstruction |120/120 PASS|proposals/diagnostic_access_verification_all_hours.json|
| Actual Word/S5scientific audit |216/216 PASS;138 S5 data cells|../02_EVIDENCE/reproducibility/document_checks/final_document_science_check.json|
| Actual Word Methods semantic audit |180/180 PASS|../02_EVIDENCE/reproducibility/document_checks/methods_semantic_check.json|
| XML/original restoration/counts/math/media/reference checks |50/50 PASS|../02_EVIDENCE/reproducibility/document_checks/document_validation.json|
| Full visual review |76 pages across clean/marked views, PASS|../02_EVIDENCE/reproducibility/document_checks/final_visual_QA.json|
| Direct diagnostic filelinks |21/21 valid|../02_EVIDENCE/reproducibility/document_checks/diagnostic_links_verified.json|

The first clean render exposed a separatedTable 2 caption; an unaccepted keep-with-next paragraph-format change fixes it. All final pages were inspected directly or matched byte-for-byte to already inspected pages; final cleanp13/14were reinspected after the repair. Main marked view has33 pages andSI17because deletions/replacement graphics remain present. QA previews are internal; no clean accepted document is delivered in place of the requested suggestions.

No computational model, threshold, source observation, existing numerical output or figure changed. The local package verifies467 inherited input/code files byte-identical to the prior corrected candidate. The earlier successful full clean-environment scientific reproduction remains evidence for those unchanged files; it was **not rerun for this editorial pass**. Fresh checks here independently reconstruct the displayed diagnostics and restricted transitions and validate the actual edited documents. No tests are claimed beyond their executed scopes.

## Local package and remaining decisions

The new local candidate isv2.1.1-r1. It preserves the existing repository folder names, updates active Word/SI inventories and adds the direct diagnostic index, S5 CSV/unrounded companion, current audit/log evidence and refreshed checksums. Prior four-table Word audit records are clearly dated history, not current-document hash assertions. The previous ZIP remains unchanged. The current Data Availability Statement and its one open author comment identifyv2.1.1-r1 as prepared, with public release pending.

Author review is the next step. No additional scientific decision is required to complete these four requested changes. The existing experimental limits remain, particularly full urban-workflow ground validation, causal attribution and final-selector unseen-city transfer. Public GitHub update/release, any deposit and journal submission still require explicit authorization. After document approval and an actual accessible release, Data Availability must be updated and final hashes refreshed; only then should the two reviewer letters and final response/line-number cross-check be prepared. No letter or submission-readiness declaration is made now.
