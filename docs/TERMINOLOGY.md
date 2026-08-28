# Terminology and notation

Use these forms consistently.

| Preferred term | Definition or note |
|---|---|
| downstream-measurand-aware harmonization | Primary method name. Define “measurand” as the quantity intended to be measured or used for scientific inference. |
| land surface temperature (LST) | Define at first use. |
| urban-core LST (`C`) | Component quantity. |
| surrounding-ring LST (`R`) | Component quantity; do not automatically call the ring peri-urban or rural. |
| core-minus-ring contrast (`D=C-R`) | Spatial downstream measurand. Use “contrast,” not “anomaly,” when precision matters. |
| pre-to-post-sunset transition (`T=D_post-D_pre`) | Temporal downstream measurand. |
| component-wise correction | Separate correction of `C` and `R`. |
| component-harmonized contrast | `D` calculated after separately harmonizing `C` and `R`. |
| direct downstream correction | Correction selected against loss for `D` or `T`. |
| raw retention | No correction applied to the downstream metric. |
| directional abstention | A sign is not supported when its empirical residual interval includes zero. |
| consistency reference | The comparison platform; never call it truth or ground truth. |
| covariance-loss penalty | `2[Cov_raw(e_c,e_r)-Cov_harm(e_c,e_r)]`; positive values reduce downstream gain. |
| crossed city-event bootstrap | Cities and events resampled independently and their multiplicities combined. |
| out-of-sample evaluation cohort | Safe collective term for the five cohorts. |
| prospectively frozen 2026 holdout | Only for the 2026 GOES-18/19 cohort. |
| outcome-blind historical external replication | Only for the fixed 2021 GOES-17/16 evaluation. |

Style conventions:

- Use `core–ring` with an en dash in prose and `core-minus-ring` only when spelling out subtraction.
- Use `harmonization` consistently in the manuscript unless the journal copy editor requests British spelling.
- Report temperatures and RMSE in kelvin (`K`); differences in Celsius and kelvin have equal numerical magnitude, but do not switch units silently.
- Typeset squared terms as `K²`, not `K2`.
- Prefer “improved agreement” or “reduced cross-platform RMSE” to “corrected the truth.”
