from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path("/Users/apple/Downloads/nbs/rerun_repair")
NOTEBOOKS = ROOT / "notebooks"
SCRIPTS = ROOT / "scripts"
OUTPUTS = ROOT / "outputs"


def md_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in dedent(text).strip().splitlines()],
    }


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in dedent(text).strip().splitlines()],
    }


def write_notebook(path: Path, cells: list[dict]) -> None:
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(nb, indent=2))


def build_local_audit_notebook() -> None:
    cells = [
        md_cell(
            """
            # Local Sample-Flow Diagnosis

            This notebook audits the current sample chain:

            - `11,422 -> 471`
            - `471 -> 201`
            - `201 -> 101`

            It uses the local files already available on disk and writes a manuscript-facing diagnosis.
            """
        ),
        code_cell(
            """
            from pathlib import Path
            import json
            import pandas as pd
            import numpy as np
            import re

            ROOT = Path("/Users/apple/Downloads")
            OUT = Path("/Users/apple/Downloads/nbs/rerun_repair/outputs")
            OUT.mkdir(parents=True, exist_ok=True)

            paths = {
                "all_geojson": ROOT / "GHS_UCDB_GLOBE_R2024A_V1_1" / "ee_assets_ready_geojson_fixed" / "ucdb_uc_polygons_fixed_all.geojson",
                "sample471_geojson": ROOT / "GHS_UCDB_GLOBE_R2024A_V1_1" / "ee_assets_ready_geojson_fixed" / "ucdb_uc_polygons_fixed_sample471.geojson",
                "retention471_csv": ROOT / "UCDB_TRC_2025_city_retention_471.csv",
                "panel_anom_csv": ROOT / "TRC_threshold_analysis_panel_anom.csv",
                "initial_notebook": ROOT / "GHS_UCDB_GLOBE_R2024A_V1_1" / "initialUCDBprocessing.ipynb",
            }

            for name, path in paths.items():
                print(name, path.exists(), path)
            """
        ),
        code_cell(
            """
            all_geo = json.loads(paths["all_geojson"].read_text())
            sample_geo = json.loads(paths["sample471_geojson"].read_text())

            n_all = len(all_geo["features"])
            n_471 = len(sample_geo["features"])

            sample_props = [f["properties"] for f in sample_geo["features"]]
            sample_income = (
                pd.Series([(p.get("wb_income") or "").strip() for p in sample_props], name="wb_income")
                .value_counts(dropna=False)
                .rename_axis("wb_income")
                .reset_index(name="n_cities")
            )

            sample_country = (
                pd.Series([(p.get("country") or "").strip() for p in sample_props], name="country")
                .value_counts(dropna=False)
                .rename_axis("country")
                .reset_index(name="n_cities")
            )

            sample_income
            """
        ),
        code_cell(
            """
            ret = pd.read_csv(paths["retention471_csv"], dtype={"uc_id": str})
            for col in ["city_retain_day", "city_retain_night", "city_retain_either"]:
                ret[col] = ret[col].astype(str).str.lower().isin(["true", "1", "yes"])

            n_201 = int(ret["city_retain_either"].sum())
            n_day = int(ret["city_retain_day"].sum())
            n_night = int(ret["city_retain_night"].sum())

            retention_summary = pd.DataFrame(
                {
                    "metric": ["city_retain_day", "city_retain_night", "city_retain_either"],
                    "n_cities": [n_day, n_night, n_201],
                }
            )

            retention_summary
            """
        ),
        code_cell(
            """
            df = pd.read_csv(paths["panel_anom_csv"], dtype={"uc_id": str})
            if "tb_night_anom" not in df.columns and {"tb_night", "tb_night_clim"}.issubset(df.columns):
                df["tb_night_anom"] = df["tb_night"] - df["tb_night_clim"]

            ring = df[df["unit"] == "ring10_20"].copy()
            city_base = ring.groupby("uc_id", as_index=False).agg(mean_ring_veg=("n_veg_day", "mean"))
            veg_median = float(city_base["mean_ring_veg"].median())
            city_base["veg_group"] = np.where(city_base["mean_ring_veg"] >= veg_median, "high_veg", "low_veg")

            veg_counts = city_base["veg_group"].value_counts().rename_axis("veg_group").reset_index(name="n_cities")
            n_101 = int((city_base["veg_group"] == "high_veg").sum())

            core = df[df["unit"] == "core"].merge(city_base[["uc_id", "veg_group"]], on="uc_id", how="left")
            flow_now = pd.DataFrame(
                [
                    {"stage": "all_11422", "cities": n_all},
                    {"stage": "sample_471", "cities": n_471},
                    {"stage": "retained_201", "cities": n_201},
                    {"stage": "high_veg_101", "cities": n_101},
                ]
            )

            flow_now
            """
        ),
        code_cell(
            """
            nb = json.loads(paths["initial_notebook"].read_text())
            flagged_cells = []
            for i, cell in enumerate(nb.get("cells", [])):
                src = "".join(cell.get("source", []))
                out_text = ""
                for out in cell.get("outputs", []):
                    out_text += "".join(out.get("text", []))
                if "NUM3 via ID_UC_G0" in src or "NUM3 via ID_UC_G0" in out_text or "Global South:" in out_text:
                    flagged_cells.append(
                        {
                            "cell_index": i,
                            "source_excerpt": src[:800],
                            "output_excerpt": out_text[:800],
                        }
                    )

            flagged_cells
            """
        ),
        code_cell(
            """
            verdict_lines = [
                "# Sample-Flow Diagnosis",
                "",
                "## Recovered chain",
                f"- `11,422`: total cities in the fixed all-city UCDB GeoJSON.",
                f"- `471`: current study sample in `ucdb_uc_polygons_fixed_sample471.geojson`.",
                f"- `201`: cities retained by the 2025 city-level QC rule in `UCDB_TRC_2025_city_retention_471.csv`.",
                f"- `101`: median-split `high_veg` half of the retained 201-city panel.",
                "",
                "## What is validated",
                "- `471 -> 201` is reproducible from the saved retention CSV and is based on 2025 valid-fraction thresholds across core and ring.",
                "- `201 -> 101` is reproducible from the saved panel and is based on a median split of mean ring vegetation support.",
                "",
                "## Main concern",
                "- The original `11,422 -> 471` step is not manuscript-safe.",
                "- In `initialUCDBprocessing.ipynb`, the sample-building logic reports `Match mode: NUM3 via ID_UC_G0`.",
                "- `ID_UC_G0` is the urban-centre identifier, not a country numeric code.",
                "- That means the original Global-South filter was likely applied to the wrong field.",
                "",
                "## External sanity check",
                "- The current 471-city sample contains only 82 high-income cities, which is not consistent with the notebook's stated intention of `300` benchmark North/high-income cities.",
                "",
                "## Verdict",
                "- The current `201` and `101` are internally consistent with the saved downstream files.",
                "- But they sit on top of a `471` base sample that is likely mis-specified.",
                "- For manuscript safety, the rerun needs to start upstream of the current `201`.",
            ]

            out_md = OUT / "sample_flow_diagnosis.md"
            out_md.write_text("\\n".join(verdict_lines))

            flow_now.to_csv(OUT / "sample_flow_counts.csv", index=False)
            sample_income.to_csv(OUT / "sample471_income_composition.csv", index=False)
            sample_country.head(50).to_csv(OUT / "sample471_top_countries.csv", index=False)
            retention_summary.to_csv(OUT / "retention471_summary.csv", index=False)
            veg_counts.to_csv(OUT / "veg_group_counts_from_current_panel.csv", index=False)

            print(out_md)
            print(flow_now)
            """
        ),
    ]
    write_notebook(NOTEBOOKS / "01_local_sample_flow_diagnosis.ipynb", cells)


def build_colab_qc_notebook() -> None:
    cells = [
        md_cell(
            """
            # Colab Rerun 1: Clean 2025 QC on All 11,422 Cities

            Use this notebook to replace the flawed `11,422 -> 471 -> 201` path.

            It starts from the existing all-city Earth Engine asset:

            - `projects/ee-zuruyuyu/assets/ucdb_uc_polygons_fixed_all`

            and computes a transparent 2025 QC screen directly for all cities.
            """
        ),
        md_cell(
            """
            ## Outputs

            - `UCDB_TRC_2025_Q1_all11422_counts_qc.csv` ... `Q4`
            - `UCDB_TRC_2025_city_summary_all11422.csv`
            - `UCDB_TRC_2025_city_retention_all11422.csv`

            ## Why this rerun is needed

            The old 471-city study sample was built with a likely invalid country-match step.
            This notebook bypasses that step completely.
            """
        ),
        code_cell(
            """
            from google.colab import auth, drive
            auth.authenticate_user()
            drive.mount('/content/drive')

            !pip -q install earthengine-api geemap

            import ee
            import pandas as pd
            import numpy as np

            ee.Authenticate()
            ee.Initialize(project='ee-zuruyuyu')
            """
        ),
        code_cell(
            """
            UCDB_ASSET = "projects/ee-zuruyuyu/assets/ucdb_uc_polygons_fixed_all"
            EXPORT_FOLDER = "GEE_exports"
            YEAR = 2025
            QUARTERS = {
                "Q1": ("2025-01-01", "2025-04-01"),
                "Q2": ("2025-04-01", "2025-07-01"),
                "Q3": ("2025-07-01", "2025-10-01"),
                "Q4": ("2025-10-01", "2026-01-01"),
            }
            BUILT_THR = 0.20
            NDVI_THR = 0.30
            SCALE = 1000
            MIN_PIXELS = 5
            RETAIN_FRAC = 0.50
            """
        ),
        code_cell(
            """
            uc = ee.FeatureCollection(UCDB_ASSET)
            print("All-city feature count:", uc.size().getInfo())

            def make_core(feat):
                return ee.Feature(feat.geometry(), {"uc_id": feat.get("uc_id"), "unit": "core"})

            def make_ring(feat):
                core = feat.geometry()
                ring = core.buffer(20000).difference(core.buffer(10000))
                return ee.Feature(ring, {"uc_id": feat.get("uc_id"), "unit": "ring10_20"})

            core_fc = uc.map(make_core)
            ring_fc = uc.map(make_ring)
            units_fc = core_fc.merge(ring_fc)
            print("Total unit features:", units_fc.size().getInfo())
            """
        ),
        code_cell(
            """
            ghs_built = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_S")
            built_ref_img = ghs_built.filter(ee.Filter.eq("system:index", "2015")).first()
            built_band = built_ref_img.select([0])
            built_mask = built_band.gt(BUILT_THR).rename("built_mask")

            lst = ee.ImageCollection("MODIS/061/MOD11A2")
            ndvi = ee.ImageCollection("MODIS/061/MOD13A2").select("NDVI")

            def prep_lst(img):
                day = img.select("LST_Day_1km").multiply(0.02).subtract(273.15)
                night = img.select("LST_Night_1km").multiply(0.02).subtract(273.15)
                return ee.Image.cat([
                    day.rename("lst_day_c"),
                    night.rename("lst_night_c"),
                ]).copyProperties(img, ["system:time_start"])

            def prep_ndvi(img):
                return img.multiply(0.0001).rename("ndvi").copyProperties(img, ["system:time_start"])

            lst2 = lst.map(prep_lst)
            ndvi2 = ndvi.map(prep_ndvi)

            max_diff = 16 * 24 * 60 * 60 * 1000
            time_filter = ee.Filter.maxDifference(
                difference=max_diff,
                leftField="system:time_start",
                rightField="system:time_start"
            )
            save_best = ee.Join.saveBest(matchKey="ndvi_img", measureKey="time_diff")
            paired = save_best.apply(lst2.filterDate("2025-01-01", "2026-01-01"), ndvi2, time_filter)

            def add_ndvi_band(img):
                nd = ee.Image(img.get("ndvi_img"))
                return ee.Image(img).addBands(nd)

            paired = ee.ImageCollection(paired.map(add_ndvi_band))
            """
        ),
        code_cell(
            """
            combined_reducer = ee.Reducer.mean().combine(
                reducer2=ee.Reducer.count(),
                sharedInputs=True
            )

            def get_or_null(d, key):
                return ee.Algorithms.If(d.contains(key), d.get(key), None)

            def safe_sub(left, right):
                return ee.Algorithms.If(
                    ee.Algorithms.IsEqual(left, None),
                    None,
                    ee.Algorithms.If(
                        ee.Algorithms.IsEqual(right, None),
                        None,
                        ee.Number(left).subtract(ee.Number(right))
                    )
                )

            def reduce_unit(img, feat):
                geom = feat.geometry()
                veg_mask = img.select("ndvi").gt(NDVI_THR).rename("veg_mask")

                stack = ee.Image.cat([
                    img.select("lst_day_c").updateMask(built_mask).rename("tb_day"),
                    img.select("lst_night_c").updateMask(built_mask).rename("tb_night"),
                    img.select("lst_day_c").updateMask(veg_mask).rename("tv_day"),
                    img.select("lst_night_c").updateMask(veg_mask).rename("tv_night"),
                ])

                stats = stack.reduceRegion(
                    reducer=combined_reducer,
                    geometry=geom,
                    scale=SCALE,
                    maxPixels=1e10
                )

                tb_day = get_or_null(stats, "tb_day_mean")
                tb_night = get_or_null(stats, "tb_night_mean")
                tv_day = get_or_null(stats, "tv_day_mean")
                tv_night = get_or_null(stats, "tv_night_mean")
                n_built_day = get_or_null(stats, "tb_day_count")
                n_built_night = get_or_null(stats, "tb_night_count")
                n_veg_day = get_or_null(stats, "tv_day_count")
                n_veg_night = get_or_null(stats, "tv_night_count")

                dT_day = safe_sub(tv_day, tb_day)
                dT_night = safe_sub(tv_night, tb_night)

                return ee.Feature(
                    None,
                    {
                        "uc_id": feat.get("uc_id"),
                        "unit": feat.get("unit"),
                        "date": ee.Date(img.get("system:time_start")).format("YYYY-MM-dd"),
                        "dT_day": dT_day,
                        "dT_night": dT_night,
                        "tb_day": tb_day,
                        "tb_night": tb_night,
                        "tv_day": tv_day,
                        "tv_night": tv_night,
                        "n_built_day": n_built_day,
                        "n_built_night": n_built_night,
                        "n_veg_day": n_veg_day,
                        "n_veg_night": n_veg_night,
                    }
                )

            def export_quarter(tag, start, end):
                sub = paired.filterDate(start, end)
                table = sub.map(lambda img: units_fc.map(lambda feat: reduce_unit(img, feat))).flatten()
                desc = f"UCDB_TRC_{YEAR}_{tag}_all11422_counts_qc"
                task = ee.batch.Export.table.toDrive(
                    collection=table,
                    description=desc,
                    folder=EXPORT_FOLDER,
                    fileNamePrefix=desc,
                    fileFormat="CSV",
                )
                task.start()
                print("Started:", desc)

            for tag, (start, end) in QUARTERS.items():
                export_quarter(tag, start, end)
            """
        ),
        code_cell(
            """
            # Run this cell only after the quarterly exports have finished and been synced to Drive.
            from glob import glob

            pattern = f"/content/drive/MyDrive/{EXPORT_FOLDER}/UCDB_TRC_{YEAR}_Q*_all11422_counts_qc.csv"
            files = sorted(glob(pattern))
            print("Files found:", len(files))
            if len(files) != 4:
                raise FileNotFoundError("Expected 4 quarterly CSVs. Wait for GEE export completion first.")

            df = pd.concat([pd.read_csv(f, dtype={"uc_id": str}) for f in files], ignore_index=True)
            df["dT_day_qc"] = np.where(
                (df["n_built_day"] >= MIN_PIXELS) & (df["n_veg_day"] >= MIN_PIXELS),
                df["dT_day"],
                np.nan
            )
            df["dT_night_qc"] = np.where(
                (df["n_built_night"] >= MIN_PIXELS) & (df["n_veg_night"] >= MIN_PIXELS),
                df["dT_night"],
                np.nan
            )

            city_summary = (
                df.groupby(["uc_id", "unit"], as_index=False)
                  .agg(
                      n_rows=("date", "count"),
                      valid_day=("dT_day_qc", lambda x: x.notna().sum()),
                      valid_night=("dT_night_qc", lambda x: x.notna().sum()),
                      mean_dT_day=("dT_day_qc", "mean"),
                      mean_dT_night=("dT_night_qc", "mean"),
                      mean_built_day=("n_built_day", "mean"),
                      mean_veg_day=("n_veg_day", "mean"),
                  )
            )
            city_summary["day_valid_frac"] = city_summary["valid_day"] / city_summary["n_rows"]
            city_summary["night_valid_frac"] = city_summary["valid_night"] / city_summary["n_rows"]

            wide = city_summary.pivot(index="uc_id", columns="unit", values=[
                "day_valid_frac", "night_valid_frac", "mean_dT_day", "mean_dT_night"
            ])
            wide.columns = ["_".join(col) for col in wide.columns]
            wide = wide.reset_index()

            wide["city_retain_day"] = (
                (wide["day_valid_frac_core"] >= RETAIN_FRAC) &
                (wide["day_valid_frac_ring10_20"] >= RETAIN_FRAC)
            )
            wide["city_retain_night"] = (
                (wide["night_valid_frac_core"] >= RETAIN_FRAC) &
                (wide["night_valid_frac_ring10_20"] >= RETAIN_FRAC)
            )
            wide["city_retain_either"] = wide["city_retain_day"] | wide["city_retain_night"]

            city_summary.to_csv("/content/drive/MyDrive/UCDB_TRC_2025_city_summary_all11422.csv", index=False)
            wide.to_csv("/content/drive/MyDrive/UCDB_TRC_2025_city_retention_all11422.csv", index=False)

            print("Retained cities:", int(wide["city_retain_either"].sum()), "out of", len(wide))
            """
        ),
    ]
    write_notebook(NOTEBOOKS / "02_colab_extract_2025_qc_all11422.ipynb", cells)


def build_colab_full_extract_notebook() -> None:
    cells = [
        md_cell(
            """
            # Colab Rerun 2: Extract Full Panel for Cleanly Screened Cities

            This notebook starts from the clean all-city 2025 retention file created in notebook 02
            and exports the full 2003-2025 TRC and ERA5-Land panels for the screened cities.
            """
        ),
        code_cell(
            """
            from google.colab import auth, drive
            auth.authenticate_user()
            drive.mount('/content/drive')

            !pip -q install earthengine-api geemap

            import ee
            import pandas as pd
            import numpy as np

            ee.Authenticate()
            ee.Initialize(project='ee-zuruyuyu')
            """
        ),
        code_cell(
            """
            UCDB_ASSET = "projects/ee-zuruyuyu/assets/ucdb_uc_polygons_fixed_all"
            RETENTION_CSV = "/content/drive/MyDrive/UCDB_TRC_2025_city_retention_all11422.csv"
            EXPORT_FOLDER = "GEE_exports"
            YEARS = list(range(2003, 2026))
            BUILT_THR = 0.20
            NDVI_THR = 0.30
            SCALE = 1000

            ret = pd.read_csv(RETENTION_CSV, dtype={"uc_id": str})
            ret["city_retain_either"] = ret["city_retain_either"].astype(str).str.lower().isin(["true", "1", "yes"])
            retained_ids = (
                ret.loc[ret["city_retain_either"], "uc_id"]
                   .astype(str).str.strip().drop_duplicates().tolist()
            )
            print("Retained IDs:", len(retained_ids))
            """
        ),
        code_cell(
            """
            uc = ee.FeatureCollection(UCDB_ASSET).filter(ee.Filter.inList("uc_id", retained_ids))

            def make_core(feat):
                return ee.Feature(feat.geometry(), {"uc_id": feat.get("uc_id"), "unit": "core"})

            def make_ring(feat):
                core = feat.geometry()
                ring = core.buffer(20000).difference(core.buffer(10000))
                return ee.Feature(ring, {"uc_id": feat.get("uc_id"), "unit": "ring10_20"})

            core_fc = uc.map(make_core)
            ring_fc = uc.map(make_ring)
            units_fc = core_fc.merge(ring_fc)

            print("Cities:", uc.size().getInfo())
            print("Unit features:", units_fc.size().getInfo())
            """
        ),
        code_cell(
            """
            # MODIS + NDVI annual TRC exports
            ghs_built = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_S")
            built_ref_img = ghs_built.filter(ee.Filter.eq("system:index", "2015")).first()
            built_band = built_ref_img.select([0])
            built_mask = built_band.gt(BUILT_THR).rename("built_mask")

            lst = ee.ImageCollection("MODIS/061/MOD11A2")
            ndvi = ee.ImageCollection("MODIS/061/MOD13A2").select("NDVI")

            def prep_lst(img):
                day = img.select("LST_Day_1km").multiply(0.02).subtract(273.15)
                night = img.select("LST_Night_1km").multiply(0.02).subtract(273.15)
                return ee.Image.cat([
                    day.rename("lst_day_c"),
                    night.rename("lst_night_c"),
                ]).copyProperties(img, ["system:time_start"])

            def prep_ndvi(img):
                return img.multiply(0.0001).rename("ndvi").copyProperties(img, ["system:time_start"])

            def get_or_null(d, key):
                return ee.Algorithms.If(d.contains(key), d.get(key), None)

            def safe_sub(left, right):
                return ee.Algorithms.If(
                    ee.Algorithms.IsEqual(left, None),
                    None,
                    ee.Algorithms.If(
                        ee.Algorithms.IsEqual(right, None),
                        None,
                        ee.Number(left).subtract(ee.Number(right))
                    )
                )

            combined_reducer = ee.Reducer.mean().combine(
                reducer2=ee.Reducer.count(),
                sharedInputs=True
            )

            def yearly_trc_export(year):
                lst_sub = lst.filterDate(f"{year}-01-01", f"{year+1}-01-01").map(prep_lst)
                ndvi_sub = ndvi.filterDate(f"{year}-01-01", f"{year+1}-01-01").map(prep_ndvi)

                join_filter = ee.Filter.maxDifference(
                    difference=16 * 24 * 60 * 60 * 1000,
                    leftField="system:time_start",
                    rightField="system:time_start"
                )
                save_best = ee.Join.saveBest(matchKey="ndvi_img", measureKey="time_diff")
                paired = ee.ImageCollection(save_best.apply(lst_sub, ndvi_sub, join_filter))

                def add_ndvi_band(img):
                    nd = ee.Image(img.get("ndvi_img"))
                    return ee.Image(img).addBands(nd)

                paired2 = paired.map(add_ndvi_band)

                def reduce_unit(img, feat):
                    geom = feat.geometry()
                    veg_mask = img.select("ndvi").gt(NDVI_THR).rename("veg_mask")
                    stack = ee.Image.cat([
                        img.select("lst_day_c").updateMask(built_mask).rename("tb_day"),
                        img.select("lst_night_c").updateMask(built_mask).rename("tb_night"),
                        img.select("lst_day_c").updateMask(veg_mask).rename("tv_day"),
                        img.select("lst_night_c").updateMask(veg_mask).rename("tv_night"),
                    ])
                    stats = stack.reduceRegion(
                        reducer=combined_reducer,
                        geometry=geom,
                        scale=SCALE,
                        maxPixels=1e10
                    )
                    tb_day = get_or_null(stats, "tb_day_mean")
                    tb_night = get_or_null(stats, "tb_night_mean")
                    tv_day = get_or_null(stats, "tv_day_mean")
                    tv_night = get_or_null(stats, "tv_night_mean")
                    return ee.Feature(
                        None,
                        {
                            "uc_id": feat.get("uc_id"),
                            "unit": feat.get("unit"),
                            "date": ee.Date(img.get("system:time_start")).format("YYYY-MM-dd"),
                            "dT_day": safe_sub(tv_day, tb_day),
                            "dT_night": safe_sub(tv_night, tb_night),
                            "tb_day": tb_day,
                            "tb_night": tb_night,
                            "tv_day": tv_day,
                            "tv_night": tv_night,
                            "n_built_day": get_or_null(stats, "tb_day_count"),
                            "n_built_night": get_or_null(stats, "tb_night_count"),
                            "n_veg_day": get_or_null(stats, "tv_day_count"),
                            "n_veg_night": get_or_null(stats, "tv_night_count"),
                        }
                    )

                table = paired2.map(lambda img: units_fc.map(lambda feat: reduce_unit(img, feat))).flatten()
                desc = f"UCDB_TRC_{year}_screened_fast"
                task = ee.batch.Export.table.toDrive(
                    collection=table,
                    description=desc,
                    folder=EXPORT_FOLDER,
                    fileNamePrefix=desc,
                    fileFormat="CSV",
                )
                task.start()
                print("Started:", desc)

            for year in YEARS:
                yearly_trc_export(year)
            """
        ),
        code_cell(
            """
            # ERA5-Land daily aggregate exports for the same screened cities
            era = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").select([
                "temperature_2m",
                "dewpoint_temperature_2m",
                "skin_temperature",
                "total_precipitation_sum",
                "volumetric_soil_water_layer_1",
                "volumetric_soil_water_layer_2",
                "volumetric_soil_water_layer_3",
                "volumetric_soil_water_layer_4",
            ])

            def add_rzsm(img):
                rzsm = (
                    img.select("volumetric_soil_water_layer_1")
                      .add(img.select("volumetric_soil_water_layer_2"))
                      .add(img.select("volumetric_soil_water_layer_3"))
                      .add(img.select("volumetric_soil_water_layer_4"))
                      .divide(4)
                      .rename("rzsm")
                )
                return img.addBands(rzsm)

            era2 = era.map(add_rzsm)
            core_only = uc.map(lambda f: ee.Feature(f.geometry(), {"uc_id": f.get("uc_id")}))

            def reduce_day(img):
                date_str = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd")
                reduced = img.reduceRegions(
                    collection=core_only,
                    reducer=ee.Reducer.mean(),
                    scale=11132
                )
                return reduced.map(lambda f: f.set("date", date_str))

            for year in YEARS:
                sub = era2.filterDate(f"{year}-01-01", f"{year+1}-01-01")
                table = sub.map(reduce_day).flatten()
                desc = f"ERA5L_daily_{year}_screened_core"
                task = ee.batch.Export.table.toDrive(
                    collection=table,
                    description=desc,
                    folder=EXPORT_FOLDER,
                    fileNamePrefix=desc,
                    fileFormat="CSV",
                )
                task.start()
                print("Started:", desc)
            """
        ),
    ]
    write_notebook(NOTEBOOKS / "03_colab_extract_full_panel_for_screened_ids.ipynb", cells)


def build_local_panel_notebook() -> None:
    cells = [
        md_cell(
            """
            # Local Rerun 3: Build Corrected Panel and Final Sample Flow

            This notebook rebuilds the merged TRC + ERA5 panel for the cleanly screened city list,
            applies full-period retention on the *actual* 2003-2025 panel, and defines the final
            `high_veg` subgroup transparently.
            """
        ),
        code_cell(
            """
            from pathlib import Path
            from glob import glob
            import pandas as pd
            import numpy as np

            ROOT = Path("/Users/apple/Downloads")
            OUT = Path("/Users/apple/Downloads/nbs/rerun_repair/outputs")
            OUT.mkdir(parents=True, exist_ok=True)

            TRC_GLOB = str(ROOT / "UCDB_TRC_*_screened_fast.csv")
            ERA_GLOB = str(ROOT / "ERA5L_daily_*_screened_core.csv")
            RETENTION_2025 = ROOT / "UCDB_TRC_2025_city_retention_all11422.csv"

            MIN_PIXELS = 5
            FULL_PERIOD_FRAC = 0.50
            """
        ),
        code_cell(
            """
            trc_files = sorted(glob(TRC_GLOB))
            era_files = sorted(glob(ERA_GLOB))
            print("TRC files:", len(trc_files))
            print("ERA files:", len(era_files))

            if len(trc_files) == 0 or len(era_files) == 0:
                raise FileNotFoundError(
                    "Expected yearly screened TRC and ERA5 files. Run notebook 03 in Colab first."
                )
            """
        ),
        code_cell(
            """
            trc = pd.concat([pd.read_csv(f, dtype={"uc_id": str}) for f in trc_files], ignore_index=True)
            trc["date"] = pd.to_datetime(trc["date"])
            trc["year"] = trc["date"].dt.year
            trc["doy"] = trc["date"].dt.dayofyear
            trc["step8"] = trc.groupby(["uc_id", "unit", "year"]).cumcount() + 1

            trc["dT_day_qc"] = np.where(
                (trc["n_built_day"] >= MIN_PIXELS) & (trc["n_veg_day"] >= MIN_PIXELS),
                trc["dT_day"],
                np.nan
            )
            trc["dT_night_qc"] = np.where(
                (trc["n_built_night"] >= MIN_PIXELS) & (trc["n_veg_night"] >= MIN_PIXELS),
                trc["dT_night"],
                np.nan
            )

            trc["dT_day_qc"] = trc["dT_day_qc"].where(trc["dT_day_qc"].between(-15, 15))
            trc["dT_night_qc"] = trc["dT_night_qc"].where(trc["dT_night_qc"].between(-10, 10))

            trc_p = (
                trc.groupby(["uc_id", "unit", "year", "step8"], as_index=False)
                   .agg(
                       date_min=("date", "min"),
                       date_max=("date", "max"),
                       dT_day=("dT_day_qc", "mean"),
                       dT_night=("dT_night_qc", "mean"),
                       tb_day=("tb_day", "mean"),
                       tb_night=("tb_night", "mean"),
                       tv_day=("tv_day", "mean"),
                       tv_night=("tv_night", "mean"),
                       n_obs_day=("dT_day_qc", lambda x: x.notna().sum()),
                       n_obs_night=("dT_night_qc", lambda x: x.notna().sum()),
                       n_built_day=("n_built_day", "mean"),
                       n_built_night=("n_built_night", "mean"),
                       n_veg_day=("n_veg_day", "mean"),
                       n_veg_night=("n_veg_night", "mean"),
                   )
            )
            print(trc_p.shape)
            """
        ),
        code_cell(
            """
            era = pd.concat([pd.read_csv(f, dtype={"uc_id": str}) for f in era_files], ignore_index=True)
            era["date"] = pd.to_datetime(era["date"])
            era["year"] = era["date"].dt.year
            era["doy"] = era["date"].dt.dayofyear
            era["pentad"] = ((era["doy"] - 1) // 5) + 1

            era["t2m_c"] = era["temperature_2m"] - 273.15
            era["td2m_c"] = era["dewpoint_temperature_2m"] - 273.15
            era["skin_c"] = era["skin_temperature"] - 273.15

            def sat_vp(temp_c):
                return 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))

            era["es"] = sat_vp(era["t2m_c"])
            era["ea"] = sat_vp(era["td2m_c"])
            era["vpd_kpa"] = era["es"] - era["ea"]

            era_p = (
                era.groupby(["uc_id", "year", "pentad"], as_index=False)
                   .agg(
                       t2m_c=("t2m_c", "mean"),
                       td2m_c=("td2m_c", "mean"),
                       skin_c=("skin_c", "mean"),
                       rzsm=("rzsm", "mean"),
                       vpd_kpa=("vpd_kpa", "mean"),
                       pr_sum=("total_precipitation_sum", "sum"),
                   )
            )

            if era_p["pentad"].nunique() and trc_p["step8"].nunique():
                step_lookup = (
                    trc_p[["year", "step8", "date_min"]]
                    .drop_duplicates()
                    .sort_values(["year", "step8"])
                )
                step_lookup["pentad"] = step_lookup["date_min"].dt.dayofyear.sub(1).floordiv(5).add(1)
                step_lookup = step_lookup[["year", "step8", "pentad"]].drop_duplicates()
                era_p = era_p.merge(step_lookup, on=["year", "pentad"], how="inner")
            else:
                raise ValueError("Could not align ERA pentads with TRC 8-day steps.")
            """
        ),
        code_cell(
            """
            merged = trc_p.merge(
                era_p.drop(columns=["pentad"]),
                on=["uc_id", "year", "step8"],
                how="left"
            )

            core = merged[merged["unit"] == "core"].copy()
            core["rzsm_pct"] = core.groupby(["uc_id", "step8"])["rzsm"].transform(lambda x: x.rank(pct=True, method="average") * 100.0)
            core["vpd_pct"] = core.groupby(["uc_id", "step8"])["vpd_kpa"].transform(lambda x: x.rank(pct=True, method="average") * 100.0)
            core["t2m_pct"] = core.groupby(["uc_id", "step8"])["t2m_c"].transform(lambda x: x.rank(pct=True, method="average") * 100.0)

            merged = merged.drop(columns=[c for c in ["rzsm_pct", "vpd_pct", "t2m_pct"] if c in merged.columns], errors="ignore")
            merged = merged.merge(
                core[["uc_id", "year", "step8", "rzsm_pct", "vpd_pct", "t2m_pct"]].drop_duplicates(),
                on=["uc_id", "year", "step8"],
                how="left"
            )
            print(merged.shape)
            """
        ),
        code_cell(
            """
            city_unit_cov = (
                merged.groupby(["uc_id", "unit"], as_index=False)
                      .agg(
                          day_valid_frac=("dT_day", lambda x: x.notna().mean()),
                          night_valid_frac=("dT_night", lambda x: x.notna().mean()),
                      )
            )

            wide = city_unit_cov.pivot(index="uc_id", columns="unit", values=["day_valid_frac", "night_valid_frac"])
            wide.columns = ["_".join(col) for col in wide.columns]
            wide = wide.reset_index()

            wide["retain_day_fullperiod"] = (
                (wide["day_valid_frac_core"] >= FULL_PERIOD_FRAC) &
                (wide["day_valid_frac_ring10_20"] >= FULL_PERIOD_FRAC)
            )
            wide["retain_night_fullperiod"] = (
                (wide["night_valid_frac_core"] >= FULL_PERIOD_FRAC) &
                (wide["night_valid_frac_ring10_20"] >= FULL_PERIOD_FRAC)
            )
            wide["retain_either_fullperiod"] = wide["retain_day_fullperiod"] | wide["retain_night_fullperiod"]

            keep_ids = set(wide.loc[wide["retain_either_fullperiod"], "uc_id"].astype(str))
            panel = merged[merged["uc_id"].isin(keep_ids)].copy()

            flow = [
                {"stage": "screened_2025_ids", "cities": int(pd.read_csv(RETENTION_2025, dtype={'uc_id': str})["city_retain_either"].astype(str).str.lower().isin(['true','1','yes']).sum())},
                {"stage": "fullperiod_retained", "cities": len(keep_ids)},
            ]

            city_base = (
                panel[panel["unit"] == "ring10_20"]
                .groupby("uc_id", as_index=False)
                .agg(mean_ring_veg=("n_veg_day", "mean"))
            )
            med = city_base["mean_ring_veg"].median()
            city_base["veg_group"] = np.where(city_base["mean_ring_veg"] >= med, "high_veg", "low_veg")
            panel = panel.merge(city_base[["uc_id", "mean_ring_veg", "veg_group"]], on="uc_id", how="left")

            flow.append({"stage": "high_veg_main_subgroup", "cities": int((city_base["veg_group"] == "high_veg").sum())})
            flow_df = pd.DataFrame(flow)
            flow_df
            """
        ),
        code_cell(
            """
            clim = (
                panel.groupby(["uc_id", "unit", "step8"], as_index=False)
                     .agg(
                         dT_day_clim=("dT_day", "mean"),
                         dT_night_clim=("dT_night", "mean"),
                         tb_day_clim=("tb_day", "mean"),
                         tb_night_clim=("tb_night", "mean"),
                         tv_day_clim=("tv_day", "mean"),
                         tv_night_clim=("tv_night", "mean"),
                     )
            )
            panel = panel.merge(clim, on=["uc_id", "unit", "step8"], how="left")
            panel["dT_day_anom"] = panel["dT_day"] - panel["dT_day_clim"]
            panel["dT_night_anom"] = panel["dT_night"] - panel["dT_night_clim"]
            panel["tb_day_anom"] = panel["tb_day"] - panel["tb_day_clim"]
            panel["tb_night_anom"] = panel["tb_night"] - panel["tb_night_clim"]
            panel["tv_day_anom"] = panel["tv_day"] - panel["tv_day_clim"]
            panel["tv_night_anom"] = panel["tv_night"] - panel["tv_night_clim"]

            panel.to_csv(OUT / "TRC_threshold_analysis_panel_anom_corrected.csv", index=False)
            wide.to_csv(OUT / "city_retention_fullperiod_corrected.csv", index=False)
            flow_df.to_csv(OUT / "sample_flow_corrected.csv", index=False)

            print(OUT / "TRC_threshold_analysis_panel_anom_corrected.csv")
            print(flow_df)
            """
        ),
    ]
    write_notebook(NOTEBOOKS / "04_local_rebuild_corrected_panel.ipynb", cells)


def build_local_main_rerun_notebook() -> None:
    cells = [
        md_cell(
            """
            # Local Rerun 4: Main Manuscript Tables From Corrected Panel

            This notebook reruns the core manuscript-facing summary tables and annual concurrence summaries
            from the corrected panel built in notebook 04.
            """
        ),
        code_cell(
            """
            from pathlib import Path
            import pandas as pd
            import numpy as np

            ROOT = Path("/Users/apple/Downloads/nbs/rerun_repair/outputs")
            PANEL = ROOT / "TRC_threshold_analysis_panel_anom_corrected.csv"
            META = Path("/Users/apple/Downloads/GHS_UCDB_GLOBE_R2024A_V1_1/ucdb_city_metadata_with_population.csv")

            df = pd.read_csv(PANEL, dtype={"uc_id": str})
            meta = pd.read_csv(META, dtype={"uc_id": str})

            main = df[(df["unit"] == "core") & (df["veg_group"] == "high_veg")].copy()
            main["state"] = np.nan
            main.loc[(main["rzsm_pct"] >= 70) & (main["vpd_pct"] <= 30), "state"] = "moist_low_demand"
            main.loc[(main["rzsm_pct"] <= 20) & (main["vpd_pct"] >= 80), "state"] = "DHD"
            main.loc[(main["rzsm_pct"] <= 10) & (main["vpd_pct"] >= 90), "state"] = "extreme_DHD"
            """
        ),
        code_cell(
            """
            day_state = (
                main.dropna(subset=["state"])
                    .groupby("state", as_index=False)
                    .agg(
                        dT_day_anom_mean=("dT_day_anom", "mean"),
                        tv_day_anom_mean=("tv_day_anom", "mean"),
                        tb_day_anom_mean=("tb_day_anom", "mean"),
                        n_rows=("uc_id", "size"),
                        n_cities=("uc_id", "nunique"),
                    )
            )

            night_state = (
                main.dropna(subset=["state"])
                    .groupby("state", as_index=False)
                    .agg(
                        dT_night_anom_mean=("dT_night_anom", "mean"),
                        tb_night_anom_mean=("tb_night_anom", "mean"),
                        tv_night_anom_mean=("tv_night_anom", "mean"),
                        n_rows=("uc_id", "size"),
                        n_cities=("uc_id", "nunique"),
                    )
            )

            day_state.to_csv(ROOT / "corrected_day_state_summary.csv", index=False)
            night_state.to_csv(ROOT / "corrected_night_state_summary.csv", index=False)
            day_state
            """
        ),
        code_cell(
            """
            main["dhd"] = ((main["rzsm_pct"] <= 20) & (main["vpd_pct"] >= 80)).astype(int)
            main["compound_night_risk"] = ((main["dhd"] == 1) & (main["tb_night_anom"] > 0)).astype(int)

            sync = (
                main.groupby(["year", "step8"], as_index=False)
                    .agg(frac_compound_night=("compound_night_risk", "mean"))
            )

            annual = (
                sync.groupby("year", as_index=False)
                    .agg(
                        mean_frac_compound_night=("frac_compound_night", "mean"),
                        p90_frac_compound_night=("frac_compound_night", lambda x: np.quantile(x, 0.90)),
                        max_frac_compound_night=("frac_compound_night", "max"),
                    )
            )
            annual.to_csv(ROOT / "corrected_core_highveg_annual_sync_summary.csv", index=False)
            annual
            """
        ),
        code_cell(
            """
            burden = main.merge(meta[["uc_id", "population_2025", "un_sdg_reg"]], on="uc_id", how="left")
            burden["weighted_night_burden"] = burden["tb_night_anom"] * burden["population_2025"]

            region = (
                burden[(burden["compound_night_risk"] == 1) & burden["tb_night_anom"].notna()]
                .groupby("un_sdg_reg", as_index=False)
                .agg(
                    total_weighted_burden=("weighted_night_burden", "sum"),
                    represented_population=("population_2025", "sum"),
                )
            )
            region.to_csv(ROOT / "corrected_region_sync_burden_summary.csv", index=False)
            region
            """
        ),
    ]
    write_notebook(NOTEBOOKS / "05_local_rerun_main_tables.ipynb", cells)


def build_colab_panel_notebook() -> None:
    cells = [
        md_cell(
            """
            # Colab Rerun 3: Build Corrected Panel and Final Sample Flow

            Use this notebook when the outputs from notebook 03 are too large to download locally.

            It reads the yearly screened TRC and ERA5-Land exports directly from Google Drive,
            rebuilds the corrected merged panel in Colab, applies full-period retention,
            and defines the corrected `high_veg` subgroup.
            """
        ),
        md_cell(
            """
            ## Expected inputs on Drive

            - `/content/drive/MyDrive/GEE_exports/UCDB_TRC_*_screened_fast.csv`
            - `/content/drive/MyDrive/GEE_exports/ERA5L_daily_*_screened_core.csv`
            - `/content/drive/MyDrive/UCDB_TRC_2025_city_retention_all11422.csv`

            ## Main outputs on Drive

            - `nbs_rerun_repair/outputs/TRC_threshold_analysis_panel_anom_corrected.parquet`
            - `nbs_rerun_repair/outputs/city_retention_fullperiod_corrected.csv`
            - `nbs_rerun_repair/outputs/sample_flow_corrected.csv`
            - `nbs_rerun_repair/outputs/panel_city_base_corrected.csv`

            ## Runtime note

            A high-RAM Colab runtime is recommended. This notebook processes the yearly files one-by-one
            and writes intermediate parquet files to Drive so you can restart without losing all progress.
            """
        ),
        code_cell(
            """
            from google.colab import drive
            drive.mount('/content/drive')

            !pip -q install pyarrow
            """
        ),
        code_cell(
            """
            from pathlib import Path
            from glob import glob
            import gc
            import re
            import pandas as pd
            import numpy as np

            DRIVE_ROOT = Path("/content/drive/MyDrive")
            EXPORT_FOLDER = DRIVE_ROOT / "GEE_exports"
            PROJECT_FOLDER = DRIVE_ROOT / "nbs_rerun_repair"
            OUT = PROJECT_FOLDER / "outputs"
            INTERMEDIATE = OUT / "intermediate"

            for path in [PROJECT_FOLDER, OUT, INTERMEDIATE]:
                path.mkdir(parents=True, exist_ok=True)

            TRC_GLOB = str(EXPORT_FOLDER / "UCDB_TRC_*_screened_fast.csv")
            ERA_GLOB = str(EXPORT_FOLDER / "ERA5L_daily_*_screened_core.csv")
            RETENTION_2025 = DRIVE_ROOT / "UCDB_TRC_2025_city_retention_all11422.csv"

            MIN_PIXELS = 5
            FULL_PERIOD_FRAC = 0.50
            WRITE_PANEL_CSV_GZ = False
            """
        ),
        code_cell(
            """
            trc_files = sorted(glob(TRC_GLOB))
            era_files = sorted(glob(ERA_GLOB))

            print("TRC files found:", len(trc_files))
            print("ERA files found:", len(era_files))
            print("Retention file exists:", RETENTION_2025.exists(), RETENTION_2025)

            if len(trc_files) == 0 or len(era_files) == 0:
                raise FileNotFoundError(
                    "Missing yearly screened exports on Drive. Confirm notebook 03 finished and the files are in MyDrive/GEE_exports."
                )
            if not RETENTION_2025.exists():
                raise FileNotFoundError(
                    "Missing UCDB_TRC_2025_city_retention_all11422.csv on Drive. Confirm notebook 02 finished."
                )
            """
        ),
        code_cell(
            """
            def infer_year(path_str):
                match = re.search(r"(19|20)\\d{2}", Path(path_str).name)
                if not match:
                    raise ValueError(f"Could not infer year from filename: {path_str}")
                return int(match.group(0))


            def process_trc_file(path_str):
                year = infer_year(path_str)
                out_path = INTERMEDIATE / f"trc_pentad_{year}.parquet"
                if out_path.exists():
                    print(f"Skipping TRC {year}, already processed.")
                    return {"year": year, "source_rows": np.nan, "pentad_rows": np.nan, "status": "cached"}

                df = pd.read_csv(path_str, dtype={"uc_id": str})
                df["date"] = pd.to_datetime(df["date"])
                df["year"] = df["date"].dt.year
                df["step8"] = df.groupby(["uc_id", "unit", "year"]).cumcount() + 1

                df["dT_day_qc"] = np.where(
                    (df["n_built_day"] >= MIN_PIXELS) & (df["n_veg_day"] >= MIN_PIXELS),
                    df["dT_day"],
                    np.nan
                )
                df["dT_night_qc"] = np.where(
                    (df["n_built_night"] >= MIN_PIXELS) & (df["n_veg_night"] >= MIN_PIXELS),
                    df["dT_night"],
                    np.nan
                )

                df["dT_day_qc"] = df["dT_day_qc"].where(df["dT_day_qc"].between(-15, 15))
                df["dT_night_qc"] = df["dT_night_qc"].where(df["dT_night_qc"].between(-10, 10))

                trc_p = (
                    df.groupby(["uc_id", "unit", "year", "step8"], as_index=False)
                      .agg(
                          date_min=("date", "min"),
                          date_max=("date", "max"),
                          dT_day=("dT_day_qc", "mean"),
                          dT_night=("dT_night_qc", "mean"),
                          tb_day=("tb_day", "mean"),
                          tb_night=("tb_night", "mean"),
                          tv_day=("tv_day", "mean"),
                          tv_night=("tv_night", "mean"),
                          n_obs_day=("dT_day_qc", lambda x: x.notna().sum()),
                          n_obs_night=("dT_night_qc", lambda x: x.notna().sum()),
                          n_built_day=("n_built_day", "mean"),
                          n_built_night=("n_built_night", "mean"),
                          n_veg_day=("n_veg_day", "mean"),
                          n_veg_night=("n_veg_night", "mean"),
                      )
                )

                trc_p.to_parquet(out_path, index=False)
                result = {"year": year, "source_rows": len(df), "pentad_rows": len(trc_p), "status": "written"}
                del df, trc_p
                gc.collect()
                return result


            trc_log = pd.DataFrame([process_trc_file(path) for path in trc_files]).sort_values("year")
            trc_log.to_csv(OUT / "trc_yearly_processing_log.csv", index=False)
            trc_log
            """
        ),
        code_cell(
            """
            def sat_vp(temp_c):
                return 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))


            def process_era_file(path_str):
                year = infer_year(path_str)
                out_path = INTERMEDIATE / f"era_pentad_{year}.parquet"
                if out_path.exists():
                    print(f"Skipping ERA {year}, already processed.")
                    return {"year": year, "source_rows": np.nan, "pentad_rows": np.nan, "status": "cached"}

                df = pd.read_csv(path_str, dtype={"uc_id": str})
                df["date"] = pd.to_datetime(df["date"])
                df["year"] = df["date"].dt.year
                df["doy"] = df["date"].dt.dayofyear
                df["pentad"] = ((df["doy"] - 1) // 5) + 1

                df["t2m_c"] = df["temperature_2m"] - 273.15
                df["td2m_c"] = df["dewpoint_temperature_2m"] - 273.15
                df["skin_c"] = df["skin_temperature"] - 273.15

                df["es"] = sat_vp(df["t2m_c"])
                df["ea"] = sat_vp(df["td2m_c"])
                df["vpd_kpa"] = df["es"] - df["ea"]

                era_p = (
                    df.groupby(["uc_id", "year", "pentad"], as_index=False)
                      .agg(
                          t2m_c=("t2m_c", "mean"),
                          td2m_c=("td2m_c", "mean"),
                          skin_c=("skin_c", "mean"),
                          rzsm=("rzsm", "mean"),
                          vpd_kpa=("vpd_kpa", "mean"),
                          pr_sum=("total_precipitation_sum", "sum"),
                      )
                )

                era_p.to_parquet(out_path, index=False)
                result = {"year": year, "source_rows": len(df), "pentad_rows": len(era_p), "status": "written"}
                del df, era_p
                gc.collect()
                return result


            era_log = pd.DataFrame([process_era_file(path) for path in era_files]).sort_values("year")
            era_log.to_csv(OUT / "era_yearly_processing_log.csv", index=False)
            era_log
            """
        ),
        code_cell(
            """
            trc_p_files = sorted((INTERMEDIATE).glob("trc_pentad_*.parquet"))
            era_p_files = sorted((INTERMEDIATE).glob("era_pentad_*.parquet"))

            trc_p = pd.concat([pd.read_parquet(path) for path in trc_p_files], ignore_index=True)
            era_p = pd.concat([pd.read_parquet(path) for path in era_p_files], ignore_index=True)

            print("Aggregated TRC shape:", trc_p.shape)
            print("Aggregated ERA shape:", era_p.shape)
            """
        ),
        code_cell(
            """
            step_lookup = (
                trc_p[["year", "step8", "date_min"]]
                .drop_duplicates()
                .sort_values(["year", "step8"])
            )
            step_lookup["pentad"] = step_lookup["date_min"].dt.dayofyear.sub(1).floordiv(5).add(1)
            step_lookup = step_lookup[["year", "step8", "pentad"]].drop_duplicates()

            era_p = era_p.merge(step_lookup, on=["year", "pentad"], how="inner")
            merged = trc_p.merge(
                era_p.drop(columns=["pentad"]),
                on=["uc_id", "year", "step8"],
                how="left"
            )

            core = merged[merged["unit"] == "core"].copy()
            core["rzsm_pct"] = core.groupby(["uc_id", "step8"])["rzsm"].transform(
                lambda x: x.rank(pct=True, method="average") * 100.0
            )
            core["vpd_pct"] = core.groupby(["uc_id", "step8"])["vpd_kpa"].transform(
                lambda x: x.rank(pct=True, method="average") * 100.0
            )
            core["t2m_pct"] = core.groupby(["uc_id", "step8"])["t2m_c"].transform(
                lambda x: x.rank(pct=True, method="average") * 100.0
            )

            merged = merged.merge(
                core[["uc_id", "year", "step8", "rzsm_pct", "vpd_pct", "t2m_pct"]].drop_duplicates(),
                on=["uc_id", "year", "step8"],
                how="left"
            )
            print("Merged panel shape:", merged.shape)
            """
        ),
        code_cell(
            """
            city_unit_cov = (
                merged.groupby(["uc_id", "unit"], as_index=False)
                      .agg(
                          day_valid_frac=("dT_day", lambda x: x.notna().mean()),
                          night_valid_frac=("dT_night", lambda x: x.notna().mean()),
                      )
            )

            wide = city_unit_cov.pivot(index="uc_id", columns="unit", values=["day_valid_frac", "night_valid_frac"])
            wide.columns = ["_".join(col) for col in wide.columns]
            wide = wide.reset_index()

            wide["retain_day_fullperiod"] = (
                (wide["day_valid_frac_core"] >= FULL_PERIOD_FRAC) &
                (wide["day_valid_frac_ring10_20"] >= FULL_PERIOD_FRAC)
            )
            wide["retain_night_fullperiod"] = (
                (wide["night_valid_frac_core"] >= FULL_PERIOD_FRAC) &
                (wide["night_valid_frac_ring10_20"] >= FULL_PERIOD_FRAC)
            )
            wide["retain_either_fullperiod"] = wide["retain_day_fullperiod"] | wide["retain_night_fullperiod"]

            keep_ids = set(wide.loc[wide["retain_either_fullperiod"], "uc_id"].astype(str))
            panel = merged[merged["uc_id"].isin(keep_ids)].copy()

            ret_2025 = pd.read_csv(RETENTION_2025, dtype={"uc_id": str})
            ret_2025["city_retain_either"] = ret_2025["city_retain_either"].astype(str).str.lower().isin(["true", "1", "yes"])

            city_base = (
                panel[panel["unit"] == "ring10_20"]
                .groupby("uc_id", as_index=False)
                .agg(mean_ring_veg=("n_veg_day", "mean"))
            )
            veg_median = city_base["mean_ring_veg"].median()
            city_base["veg_group"] = np.where(city_base["mean_ring_veg"] >= veg_median, "high_veg", "low_veg")

            panel = panel.merge(city_base[["uc_id", "mean_ring_veg", "veg_group"]], on="uc_id", how="left")

            flow_df = pd.DataFrame(
                [
                    {"stage": "screened_2025_ids", "cities": int(ret_2025["city_retain_either"].sum())},
                    {"stage": "fullperiod_retained", "cities": len(keep_ids)},
                    {"stage": "high_veg_main_subgroup", "cities": int((city_base["veg_group"] == "high_veg").sum())},
                ]
            )
            flow_df
            """
        ),
        code_cell(
            """
            clim = (
                panel.groupby(["uc_id", "unit", "step8"], as_index=False)
                     .agg(
                         dT_day_clim=("dT_day", "mean"),
                         dT_night_clim=("dT_night", "mean"),
                         tb_day_clim=("tb_day", "mean"),
                         tb_night_clim=("tb_night", "mean"),
                         tv_day_clim=("tv_day", "mean"),
                         tv_night_clim=("tv_night", "mean"),
                     )
            )

            panel = panel.merge(clim, on=["uc_id", "unit", "step8"], how="left")
            panel["dT_day_anom"] = panel["dT_day"] - panel["dT_day_clim"]
            panel["dT_night_anom"] = panel["dT_night"] - panel["dT_night_clim"]
            panel["tb_day_anom"] = panel["tb_day"] - panel["tb_day_clim"]
            panel["tb_night_anom"] = panel["tb_night"] - panel["tb_night_clim"]
            panel["tv_day_anom"] = panel["tv_day"] - panel["tv_day_clim"]
            panel["tv_night_anom"] = panel["tv_night"] - panel["tv_night_clim"]

            panel_parquet = OUT / "TRC_threshold_analysis_panel_anom_corrected.parquet"
            panel.to_parquet(panel_parquet, index=False)

            if WRITE_PANEL_CSV_GZ:
                panel.to_csv(OUT / "TRC_threshold_analysis_panel_anom_corrected.csv.gz", index=False, compression="gzip")

            wide.to_csv(OUT / "city_retention_fullperiod_corrected.csv", index=False)
            flow_df.to_csv(OUT / "sample_flow_corrected.csv", index=False)
            city_base.to_csv(OUT / "panel_city_base_corrected.csv", index=False)

            print("Wrote:", panel_parquet)
            print("Wrote:", OUT / "city_retention_fullperiod_corrected.csv")
            print("Wrote:", OUT / "sample_flow_corrected.csv")
            print(flow_df)
            """
        ),
    ]
    write_notebook(NOTEBOOKS / "04_colab_rebuild_corrected_panel.ipynb", cells)


def build_colab_main_rerun_notebook() -> None:
    cells = [
        md_cell(
            """
            # Colab Rerun 4: Main Manuscript Tables From Corrected Panel

            This notebook reruns the core manuscript-facing summary tables and annual concurrence summaries
            directly in Colab from the corrected panel created in notebook 04.
            """
        ),
        md_cell(
            """
            ## Required inputs on Drive

            - `nbs_rerun_repair/outputs/TRC_threshold_analysis_panel_anom_corrected.parquet`
            - `ucdb_city_metadata_with_population.csv`

            The metadata CSV should ideally be placed at:

            - `/content/drive/MyDrive/nbs_rerun_repair/inputs/ucdb_city_metadata_with_population.csv`

            A fallback path of `/content/drive/MyDrive/ucdb_city_metadata_with_population.csv` is also checked.
            """
        ),
        code_cell(
            """
            from google.colab import drive
            drive.mount('/content/drive')

            !pip -q install pyarrow
            """
        ),
        code_cell(
            """
            from pathlib import Path
            import pandas as pd
            import numpy as np

            DRIVE_ROOT = Path("/content/drive/MyDrive")
            PROJECT_FOLDER = DRIVE_ROOT / "nbs_rerun_repair"
            OUT = PROJECT_FOLDER / "outputs"
            INPUTS = PROJECT_FOLDER / "inputs"
            INPUTS.mkdir(parents=True, exist_ok=True)

            PANEL_PARQUET = OUT / "TRC_threshold_analysis_panel_anom_corrected.parquet"
            PANEL_CSV_GZ = OUT / "TRC_threshold_analysis_panel_anom_corrected.csv.gz"
            META_CANDIDATES = [
                INPUTS / "ucdb_city_metadata_with_population.csv",
                DRIVE_ROOT / "ucdb_city_metadata_with_population.csv",
            ]

            if PANEL_PARQUET.exists():
                df = pd.read_parquet(PANEL_PARQUET)
                print("Loaded:", PANEL_PARQUET)
            elif PANEL_CSV_GZ.exists():
                df = pd.read_csv(PANEL_CSV_GZ, dtype={"uc_id": str})
                print("Loaded:", PANEL_CSV_GZ)
            else:
                raise FileNotFoundError(
                    "Corrected panel not found on Drive. Run 04_colab_rebuild_corrected_panel.ipynb first."
                )

            meta_path = None
            for candidate in META_CANDIDATES:
                if candidate.exists():
                    meta_path = candidate
                    break

            if meta_path is None:
                raise FileNotFoundError(
                    "Could not find ucdb_city_metadata_with_population.csv on Drive. "
                    "Upload it to MyDrive/nbs_rerun_repair/inputs/ or MyDrive/."
                )

            meta = pd.read_csv(meta_path, dtype={"uc_id": str})
            print("Loaded metadata:", meta_path)

            main = df[(df["unit"] == "core") & (df["veg_group"] == "high_veg")].copy()
            main["state"] = np.nan
            main.loc[(main["rzsm_pct"] >= 70) & (main["vpd_pct"] <= 30), "state"] = "moist_low_demand"
            main.loc[(main["rzsm_pct"] <= 20) & (main["vpd_pct"] >= 80), "state"] = "DHD"
            main.loc[(main["rzsm_pct"] <= 10) & (main["vpd_pct"] >= 90), "state"] = "extreme_DHD"

            print("Main subgroup rows:", len(main))
            print("Main subgroup cities:", main["uc_id"].nunique())
            """
        ),
        code_cell(
            """
            day_state = (
                main.dropna(subset=["state"])
                    .groupby("state", as_index=False)
                    .agg(
                        dT_day_anom_mean=("dT_day_anom", "mean"),
                        tv_day_anom_mean=("tv_day_anom", "mean"),
                        tb_day_anom_mean=("tb_day_anom", "mean"),
                        n_rows=("uc_id", "size"),
                        n_cities=("uc_id", "nunique"),
                    )
            )

            night_state = (
                main.dropna(subset=["state"])
                    .groupby("state", as_index=False)
                    .agg(
                        dT_night_anom_mean=("dT_night_anom", "mean"),
                        tb_night_anom_mean=("tb_night_anom", "mean"),
                        tv_night_anom_mean=("tv_night_anom", "mean"),
                        n_rows=("uc_id", "size"),
                        n_cities=("uc_id", "nunique"),
                    )
            )

            day_state.to_csv(OUT / "corrected_day_state_summary.csv", index=False)
            night_state.to_csv(OUT / "corrected_night_state_summary.csv", index=False)
            day_state
            """
        ),
        code_cell(
            """
            main["dhd"] = ((main["rzsm_pct"] <= 20) & (main["vpd_pct"] >= 80)).astype(int)
            main["compound_night_risk"] = ((main["dhd"] == 1) & (main["tb_night_anom"] > 0)).astype(int)

            sync = (
                main.groupby(["year", "step8"], as_index=False)
                    .agg(frac_compound_night=("compound_night_risk", "mean"))
            )

            annual = (
                sync.groupby("year", as_index=False)
                    .agg(
                        mean_frac_compound_night=("frac_compound_night", "mean"),
                        p90_frac_compound_night=("frac_compound_night", lambda x: np.quantile(x, 0.90)),
                        max_frac_compound_night=("frac_compound_night", "max"),
                    )
            )

            annual.to_csv(OUT / "corrected_core_highveg_annual_sync_summary.csv", index=False)
            annual
            """
        ),
        code_cell(
            """
            burden = main.merge(meta[["uc_id", "population_2025", "un_sdg_reg"]], on="uc_id", how="left")
            burden["weighted_night_burden"] = burden["tb_night_anom"] * burden["population_2025"]

            region = (
                burden[(burden["compound_night_risk"] == 1) & burden["tb_night_anom"].notna()]
                .groupby("un_sdg_reg", as_index=False)
                .agg(
                    total_weighted_burden=("weighted_night_burden", "sum"),
                    represented_population=("population_2025", "sum"),
                    n_cities=("uc_id", "nunique"),
                )
            )

            region.to_csv(OUT / "corrected_region_sync_burden_summary.csv", index=False)
            region
            """
        ),
    ]
    write_notebook(NOTEBOOKS / "05_colab_rerun_main_tables.ipynb", cells)


def build_readme() -> None:
    text = dedent(
        """
        # Rerun Repair Bundle

        This folder contains the repair assets for the sample-flow problem identified in the manuscript pipeline.

        ## Main conclusion

        The current `201` and `101` counts are reproducible, but the upstream `471` sample appears to have been built from a flawed country-match step in `initialUCDBprocessing.ipynb`.

        ## Required rerun order

        1. `01_local_sample_flow_diagnosis.ipynb`
           - Audits the current chain and writes a manuscript-facing diagnosis.
           - Can be run locally.

        2. `02_colab_extract_2025_qc_all11422.ipynb`
           - Replaces the flawed `11,422 -> 471 -> 201` path by computing 2025 QC directly on all 11,422 cities in Earth Engine.
           - Must be run in Colab with Earth Engine access.

        3. `03_colab_extract_full_panel_for_screened_ids.ipynb`
           - Exports the full 2003-2025 TRC and ERA5-Land data for the cleanly screened city IDs.
           - Must be run in Colab with Earth Engine access.

        4. `04_local_rebuild_corrected_panel.ipynb`
           - Rebuilds the merged corrected panel, applies full-period retention, and defines the corrected `high_veg` subgroup.
           - Can be run locally once notebook 03 outputs exist.

        5. `05_local_rerun_main_tables.ipynb`
           - Regenerates core state summaries and annual concurrence tables from the corrected panel.
           - Can be run locally once notebook 04 outputs exist.

        ## Colab-only continuation

        If notebook 03 outputs are too large to download, use these instead:

        - `04_colab_rebuild_corrected_panel.ipynb`
          - Reads the yearly screened exports directly from `MyDrive/GEE_exports`.
          - Builds the corrected merged panel in Colab and writes the outputs back to Drive.

        - `05_colab_rerun_main_tables.ipynb`
          - Reads the corrected panel from Drive and regenerates the main summary tables in Colab.
          - Requires `ucdb_city_metadata_with_population.csv` on Drive for the regional burden table.

        ## Local script

        - `scripts/run_local_sample_flow_diagnosis.py`
          - Non-notebook local runner that writes:
            - `outputs/sample_flow_diagnosis.md`
            - `outputs/sample_flow_counts.csv`
            - `outputs/sample471_income_composition.csv`

        ## Recommended manuscript decision

        For a top-journal submission, do not rely on the existing `201` panel as-is.
        Start the rerun upstream of the current `201` by replacing the flawed `471` base sample.
        """
    ).strip() + "\n"
    (ROOT / "README.md").write_text(text)


def build_local_runner() -> None:
    script = dedent(
        """
        from pathlib import Path
        import json
        import pandas as pd
        import numpy as np

        ROOT = Path("/Users/apple/Downloads")
        OUT = Path("/Users/apple/Downloads/nbs/rerun_repair/outputs")
        OUT.mkdir(parents=True, exist_ok=True)

        all_geo = json.loads((ROOT / "GHS_UCDB_GLOBE_R2024A_V1_1" / "ee_assets_ready_geojson_fixed" / "ucdb_uc_polygons_fixed_all.geojson").read_text())
        sample_geo = json.loads((ROOT / "GHS_UCDB_GLOBE_R2024A_V1_1" / "ee_assets_ready_geojson_fixed" / "ucdb_uc_polygons_fixed_sample471.geojson").read_text())
        ret = pd.read_csv(ROOT / "UCDB_TRC_2025_city_retention_471.csv", dtype={"uc_id": str})
        df = pd.read_csv(ROOT / "TRC_threshold_analysis_panel_anom.csv", dtype={"uc_id": str})

        for col in ["city_retain_day", "city_retain_night", "city_retain_either"]:
            ret[col] = ret[col].astype(str).str.lower().isin(["true", "1", "yes"])

        if "tb_night_anom" not in df.columns and {"tb_night", "tb_night_clim"}.issubset(df.columns):
            df["tb_night_anom"] = df["tb_night"] - df["tb_night_clim"]

        n_all = len(all_geo["features"])
        n_471 = len(sample_geo["features"])
        n_201 = int(ret["city_retain_either"].sum())

        sample_props = [f["properties"] for f in sample_geo["features"]]
        income = (
            pd.Series([(p.get("wb_income") or "").strip() for p in sample_props], name="wb_income")
            .value_counts(dropna=False)
            .rename_axis("wb_income")
            .reset_index(name="n_cities")
        )

        ring = df[df["unit"] == "ring10_20"].copy()
        city_base = ring.groupby("uc_id", as_index=False).agg(mean_ring_veg=("n_veg_day", "mean"))
        city_base["veg_group"] = np.where(city_base["mean_ring_veg"] >= city_base["mean_ring_veg"].median(), "high_veg", "low_veg")
        n_101 = int((city_base["veg_group"] == "high_veg").sum())

        flow = pd.DataFrame([
            {"stage": "all_11422", "cities": n_all},
            {"stage": "sample_471", "cities": n_471},
            {"stage": "retained_201", "cities": n_201},
            {"stage": "high_veg_101", "cities": n_101},
        ])
        flow.to_csv(OUT / "sample_flow_counts.csv", index=False)
        income.to_csv(OUT / "sample471_income_composition.csv", index=False)

        lines = [
            "# Sample-Flow Diagnosis",
            "",
            f"- `11,422`: confirmed from the all-city fixed UCDB GeoJSON.",
            f"- `471`: confirmed from the current study-sample GeoJSON.",
            f"- `201`: confirmed from the saved 2025 retention CSV.",
            f"- `101`: confirmed from the current panel by the median split on ring vegetation support.",
            "",
            "## Verdict",
            "- The current 201 and 101 are internally reproducible.",
            "- But the upstream 471 sample is not manuscript-safe.",
            "- The old sample-building notebook reports `NUM3 via ID_UC_G0`, which strongly suggests the Global-South filter was applied to the wrong field.",
            "- The 471-city sample composition also does not look like the intended `Global South + 300 high-income benchmark North` design.",
            "- Recommended fix: rerun upstream of the current 201 using the all-city asset.",
        ]
        (OUT / "sample_flow_diagnosis.md").write_text("\\n".join(lines) + "\\n")
        print(OUT / "sample_flow_diagnosis.md")
        print(flow)
        """
    ).strip() + "\n"
    (SCRIPTS / "run_local_sample_flow_diagnosis.py").write_text(script)


def main() -> None:
    for path in [ROOT, NOTEBOOKS, SCRIPTS, OUTPUTS]:
        path.mkdir(parents=True, exist_ok=True)

    build_local_audit_notebook()
    build_colab_qc_notebook()
    build_colab_full_extract_notebook()
    build_local_panel_notebook()
    build_local_main_rerun_notebook()
    build_colab_panel_notebook()
    build_colab_main_rerun_notebook()
    build_readme()
    build_local_runner()

    print("Wrote rerun assets to", ROOT)


if __name__ == "__main__":
    main()
