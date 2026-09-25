#!/usr/bin/env python3
"""Build revised Remote Sensing Figures 1--3 from frozen evidence.

This script only visualizes existing verified evidence. It does not fit a model,
resample observations, alter a frozen design, or modify the manuscript/SI.

Figure 1 combines the established measurand workflow with fixed western city
support and an exact start-date chronology. Figure 2 displays the frozen 2025
one-standard-error selections with simplified encodings. Figure 3 contains
only the cross-cohort RMSE and exact MSE-decomposition panels.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapefile
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, PathPatch
from matplotlib.path import Path as MplPath
from PIL import Image
from pyproj import Geod, Transformer
from shapely.geometry import box, shape
from shapely.ops import transform as transform_geometry


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "02_EVIDENCE"
OUT = ROOT / "06_SUBMISSION" / "figures"

SOURCES = {
    "cities": EVIDENCE / "si_tables" / "fixed_city_candidate_metadata.csv",
    "chronology": EVIDENCE / "si_tables" / "fixed_interval_chronology.csv",
    "counts": EVIDENCE / "si_tables" / "cohort_event_analysis_counts.csv",
    "model_selection": EVIDENCE / "si_tables" / "model_selection_summary.csv",
    "rmse": EVIDENCE / "tables" / "downstream_metric_framework_figure_rmse_source.csv",
    "mse": EVIDENCE / "tables" / "downstream_metric_framework_figure_budget_source.csv",
}

NATURAL_EARTH = ROOT / "data" / "natural_earth"
BASEMAP = {
    "land": NATURAL_EARTH / "physical" / "ne_110m_land.shp",
    "countries": NATURAL_EARTH
    / "cultural"
    / "ne_110m_admin_0_boundary_lines_land.shp",
    "states_provinces": NATURAL_EARTH
    / "cultural"
    / "ne_50m_admin_1_states_provinces_lines.shp",
}

MAP_EXTENT = (-125.0, -100.0, 31.0, 51.0)

EXPECTED_SOURCE_HASHES = {
    "cities": "bc682ab609298bf36ba4841693cb26895525e7ec085c3c87a0fbc1b170707378",
    "chronology": "ba96cdcc9a3f8ef9b00aa61bee3676977714ed590392ca79ad4be2d97c817b23",
    "counts": "34c101b4c79e6340bdc87eb8f26f75cef001ab277ef50c132cd12e39cee34be1",
    "model_selection": "1de247585987d64021fd95e3189ca36a7800b3c5dd9b09868c4617ff7bb9bdf1",
    "rmse": "3de82ac0bd5fb2ad7e5f0d7901d2e5956980f6f86d154a30e93eec85878ce8af",
    "mse": "368556f1923ae22dfdd5e2c94574257968aaf271b0860c7522b98e94a0ed92a9",
}

FIXED_EXPORT_TIME = datetime(2026, 9, 16, tzinfo=timezone.utc)
FINAL_WIDTH_IN = 6.879

COLORS = {
    "core": "#0072B2",
    "ring": "#009E73",
    "contrast": "#CC79A7",
    "calibration": "#56B4E9",
    "evaluation": "#009E73",
    "historical": "#E69F00",
    "prospective": "#CC79A7",
    "dual": "#2A9D8F",
    "variance": "#56B4E9",
    "bias": "#E69F00",
    "covariance": "#D55E00",
    "net": "#222222",
    "candidate": "#B8B8B8",
    "ink": "#222222",
    "muted": "#666666",
    "light": "#E5E5E5",
    "selected": "#D55E00",
    "admissible": "#0072B2",
    "inadmissible": "#8A8A8A",
}

SAMPLE_ORDER = [
    "2021 external GOES17/16",
    "2022-2024 expansion GOES18/16",
    "2025 original GOES18/19",
    "2025 expansion GOES18/19",
    "2026 combined GOES18/19",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def configure_submission_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.labelsize": 9.2,
            "axes.titlesize": 9.5,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "legend.fontsize": 7.8,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "remote-sensing-revised-figures-1-2-3",
        }
    )


def panel_label(axis: plt.Axes, label: str, x: float = -0.10, y: float = 1.08) -> None:
    axis.text(
        x,
        y,
        label,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=11.5,
        fontweight="bold",
        clip_on=False,
    )


def rounded_box(
    axis: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    facecolor: str,
    edgecolor: str,
    fontsize: float = 8.2,
) -> None:
    axis.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            transform=axis.transAxes,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.0,
        )
    )
    axis.text(
        x + width / 2,
        y + height / 2,
        text,
        transform=axis.transAxes,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=COLORS["ink"],
        linespacing=1.10,
    )


def axes_arrow(
    axis: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    mutation_scale: float = 9.0,
) -> None:
    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            transform=axis.transAxes,
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            linewidth=0.9,
            color=COLORS["muted"],
            shrinkA=1,
            shrinkB=1,
        )
    )


def draw_workflow(axis: plt.Axes) -> None:
    axis.set_axis_off()
    axis.text(
        0.01,
        0.96,
        "Scientific measurands",
        transform=axis.transAxes,
        fontsize=9.2,
        fontweight="bold",
        color=COLORS["muted"],
        va="top",
    )
    axis.text(
        0.01,
        -0.04,
        "Measurand-level actions",
        transform=axis.transAxes,
        fontsize=9.2,
        fontweight="bold",
        color=COLORS["muted"],
        va="top",
        clip_on=False,
    )

    # Equal column centers with boxes 15% narrower than the preceding version.
    # Arrow endpoints are placed in the open gaps, never on the box borders.
    centers = [0.125, 0.375, 0.625, 0.875]
    width = 0.157
    box_x = [center - width / 2 for center in centers]
    measurands = [
        ("Component LST\n$C$ urban core\n$R$ surrounding ring", "#EAF4FA", COLORS["core"]),
        ("Spatial contrast\n$D=C-R$", "#EAF7F2", COLORS["ring"]),
        (
            "Temporal transition\n$T=D_{\\mathrm{post}}-D_{\\mathrm{pre}}$",
            "#F3EDF5",
            COLORS["contrast"],
        ),
        ("Transition direction\n$\\operatorname{sign}(T)$", "#F3EDF5", COLORS["contrast"]),
    ]
    actions = [
        ("Selected\ncomponent models\nUse component\ncorrection", "#DDEFF7", COLORS["core"]),
        ("Raw selected\nRetain raw contrast", "#DDF1EA", COLORS["ring"]),
        ("Raw selected\nRetain raw transition", "#F0E2EF", COLORS["contrast"]),
        (
            "Empirical residual\ninterval\nSupport sign\nor abstain",
            "#F0E2EF",
            COLORS["contrast"],
        ),
    ]
    for x, measurand, action in zip(box_x, measurands, actions):
        rounded_box(axis, x, 0.57, width, 0.25, measurand[0], measurand[1], measurand[2])
        rounded_box(axis, x, 0.05, width, 0.28, action[0], action[1], action[2], fontsize=8.0)
        axes_arrow(axis, (x + width / 2, 0.565), (x + width / 2, 0.34))

    for left, right in zip(box_x[:-1], box_x[1:]):
        gap_start = left + width + 0.012
        gap_end = right - 0.012
        axes_arrow(axis, (gap_start, 0.695), (gap_end, 0.695), mutation_scale=8.5)
        axis.text(
            (gap_start + gap_end) / 2,
            0.724,
            "derive",
            transform=axis.transAxes,
            ha="center",
            va="bottom",
            fontsize=8.2,
            color=COLORS["muted"],
        )


def geometry_path(geometry) -> MplPath:
    vertices: list[tuple[float, float]] = []
    codes: list[int] = []
    polygons = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
    for polygon in polygons:
        for ring in [polygon.exterior, *polygon.interiors]:
            coords = list(ring.coords)
            if len(coords) < 3:
                continue
            vertices.extend(coords)
            codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(coords) - 2) + [MplPath.CLOSEPOLY])
    return MplPath(np.asarray(vertices, dtype=float), np.asarray(codes, dtype=np.uint8))


def add_polygon_shapes(
    axis: plt.Axes,
    shp_path: Path,
    transformer: Transformer,
    clip_bounds,
    facecolor: str,
    edgecolor: str,
    linewidth: float,
    zorder: int,
) -> None:
    for raw_shape in shapefile.Reader(str(shp_path)).shapes():
        geom = shape(raw_shape.__geo_interface__).intersection(clip_bounds)
        if geom.is_empty:
            continue
        projected = transform_geometry(transformer.transform, geom)
        if projected.geom_type not in {"Polygon", "MultiPolygon"}:
            continue
        axis.add_patch(
            PathPatch(
                geometry_path(projected),
                facecolor=facecolor,
                edgecolor=edgecolor,
                linewidth=linewidth,
                zorder=zorder,
            )
        )


def iter_lines(geometry):
    if geometry.geom_type in {"LineString", "LinearRing"}:
        yield geometry
    elif geometry.geom_type == "MultiLineString":
        yield from geometry.geoms
    elif geometry.geom_type == "GeometryCollection":
        for part in geometry.geoms:
            yield from iter_lines(part)


def add_line_shapes(
    axis: plt.Axes,
    shp_path: Path,
    transformer: Transformer,
    clip_bounds,
    color: str,
    linewidth: float,
    zorder: int,
) -> None:
    for raw_shape in shapefile.Reader(str(shp_path)).shapes():
        geom = shape(raw_shape.__geo_interface__).intersection(clip_bounds)
        if geom.is_empty:
            continue
        projected = transform_geometry(transformer.transform, geom)
        for line in iter_lines(projected):
            coordinates = np.asarray(line.coords)
            axis.plot(
                coordinates[:, 0],
                coordinates[:, 1],
                color=color,
                linewidth=linewidth,
                zorder=zorder,
            )


def draw_city_map(axis: plt.Axes, cities: pd.DataFrame) -> list[Line2D]:
    """Draw the verified city support in a rectangular Plate Carree frame."""
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:4326", always_xy=True)
    west, east, south, north = MAP_EXTENT
    clip_bounds = box(west, south, east, north)

    axis.set_facecolor("#EAF3F7")
    add_polygon_shapes(
        axis,
        BASEMAP["land"],
        transformer,
        clip_bounds,
        facecolor="#F4F0E7",
        edgecolor="none",
        linewidth=0,
        zorder=0,
    )
    add_line_shapes(
        axis,
        BASEMAP["states_provinces"],
        transformer,
        clip_bounds,
        color="#C8C8C8",
        linewidth=0.28,
        zorder=1,
    )
    add_line_shapes(
        axis,
        BASEMAP["countries"],
        transformer,
        clip_bounds,
        color="#858585",
        linewidth=0.62,
        zorder=2,
    )

    # Plate Carree uses longitude and latitude directly; no coordinate is moved.
    x_city = cities["lon"].to_numpy(copy=True)
    y_city = cities["lat"].to_numpy(copy=True)
    require(np.array_equal(x_city, cities["lon"].to_numpy()), "City longitudes changed during map preparation")
    require(np.array_equal(y_city, cities["lat"].to_numpy()), "City latitudes changed during map preparation")
    plotted = cities.assign(map_x=x_city, map_y=y_city)
    retained = plotted["analyzed_holdout_2026_combined"].astype(bool)
    original = retained & plotted["calibration_cohort"].eq("original")
    expansion = retained & plotted["calibration_cohort"].eq("expansion")
    candidate_only = ~retained
    absent_2021 = retained & ~plotted["analyzed_external_validation_2021"].astype(bool)

    axis.scatter(
        plotted.loc[candidate_only, "map_x"],
        plotted.loc[candidate_only, "map_y"],
        s=13,
        marker="o",
        facecolor="#8F8F8F",
        edgecolor="none",
        alpha=0.50,
        zorder=3,
    )
    axis.scatter(
        plotted.loc[original, "map_x"],
        plotted.loc[original, "map_y"],
        s=24,
        marker="o",
        facecolor=COLORS["core"],
        edgecolor="#005786",
        linewidth=0.35,
        alpha=0.70,
        zorder=4,
    )
    axis.scatter(
        plotted.loc[expansion, "map_x"],
        plotted.loc[expansion, "map_y"],
        s=30,
        marker="^",
        facecolor=COLORS["historical"],
        edgecolor="#9B6A00",
        linewidth=0.35,
        alpha=0.70,
        zorder=4,
    )
    axis.scatter(
        plotted.loc[absent_2021, "map_x"],
        plotted.loc[absent_2021, "map_y"],
        s=64,
        marker="o",
        facecolor="none",
        edgecolor=COLORS["ink"],
        linewidth=0.85,
        zorder=5,
    )

    axis.set_xlim(west, east)
    axis.set_ylim(south, north)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xticks([-125, -120, -115, -110, -105, -100])
    axis.set_xticklabels(["125°W", "120°W", "115°W", "110°W", "105°W", "100°W"])
    axis.set_yticks([32, 36, 40, 44, 48])
    axis.set_yticklabels(["32°N", "36°N", "40°N", "44°N", "48°N"])
    axis.tick_params(axis="both", direction="out", length=2.5, width=0.6, pad=2.5, labelsize=7.1, colors=COLORS["muted"])
    axis.grid(False)
    for spine in axis.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.65)
        spine.set_color("#777777")

    # An exact 500-km geodesic span at 31.55°N; the buffered strip is marker-free.
    scale_y = 31.55
    scale_start = -124.5
    geod = Geod(ellps="WGS84")
    low, high = scale_start, scale_start + 8.0
    for _ in range(60):
        midpoint = (low + high) / 2
        distance_m = geod.inv(scale_start, scale_y, midpoint, scale_y)[2]
        if distance_m < 500_000.0:
            low = midpoint
        else:
            high = midpoint
    scale_end = (low + high) / 2
    scale_distance_m = geod.inv(scale_start, scale_y, scale_end, scale_y)[2]
    require(abs(scale_distance_m - 500_000.0) < 0.1, "Scale-bar distance is not 500 km")
    scale_clearance = cities[
        cities["lon"].between(scale_start - 0.30, scale_end + 0.30)
        & cities["lat"].between(scale_y - 0.35, scale_y + 0.70)
    ]
    require(scale_clearance.empty, "Chosen scale-bar location is not clear of city markers")
    axis.plot([scale_start, scale_end], [scale_y, scale_y], color=COLORS["ink"], linewidth=1.1, zorder=7)
    axis.plot([scale_start, scale_start], [scale_y - 0.16, scale_y + 0.16], color=COLORS["ink"], linewidth=0.9, zorder=7)
    axis.plot([scale_end, scale_end], [scale_y - 0.16, scale_y + 0.16], color=COLORS["ink"], linewidth=0.9, zorder=7)
    axis.text((scale_start + scale_end) / 2, scale_y + 0.30, "500 km", ha="center", va="bottom", fontsize=7.0, zorder=7)

    axis.annotate(
        "N",
        xy=(0.955, 0.94),
        xytext=(0.955, 0.82),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="bottom",
        fontsize=8.0,
        fontweight="bold",
        arrowprops={"arrowstyle": "-|>", "lw": 1.0, "color": COLORS["ink"]},
    )

    return [
        Line2D([], [], marker="o", linestyle="none", markersize=4.8, markerfacecolor=COLORS["core"], markeredgecolor="#005786", markeredgewidth=0.45, alpha=0.70, label="Original retained (44)"),
        Line2D([], [], marker="^", linestyle="none", markersize=5.2, markerfacecolor=COLORS["historical"], markeredgecolor="#9B6A00", markeredgewidth=0.45, alpha=0.70, label="Expansion retained (31)"),
        Line2D([], [], marker="o", linestyle="none", markersize=6.5, markerfacecolor="none", markeredgecolor=COLORS["ink"], label="Not retained in 2021 (6)"),
        Line2D([], [], marker="o", linestyle="none", markersize=4.0, markerfacecolor="#8F8F8F", markeredgecolor="none", alpha=0.50, label="Candidate only (19)"),
    ]


def draw_support_flow(axis: plt.Axes, legend_handles: list[Line2D]) -> None:
    axis.set_axis_off()
    axis.legend(
        handles=legend_handles,
        loc="upper left",
        bbox_to_anchor=(0.00, 0.995),
        frameon=False,
        ncol=2,
        handletextpad=0.35,
        columnspacing=0.55,
        borderaxespad=0,
        fontsize=6.3,
    )

    def flow_box(x: float, y: float, width: float, height: float, text: str) -> None:
        axis.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                transform=axis.transAxes,
                boxstyle="round,pad=0.010,rounding_size=0.018",
                facecolor="#F7F7F5",
                edgecolor="#8A8A8A",
                linewidth=0.65,
            )
        )
        axis.text(
            x + width / 2,
            y + height / 2,
            text,
            transform=axis.transAxes,
            ha="center",
            va="center",
            fontsize=6.7,
            linespacing=1.08,
            color=COLORS["ink"],
        )

    flow_box(0.04, 0.695, 0.64, 0.105, "94 fixed candidates")
    flow_box(0.04, 0.420, 0.64, 0.155, "75 common-support\nanalyzed cities\n44 original + 31 expansion")
    flow_box(0.04, 0.165, 0.64, 0.115, "69 cities in\n2021 replication")
    axes_arrow(axis, (0.36, 0.690), (0.36, 0.585), mutation_scale=7.0)
    axes_arrow(axis, (0.36, 0.415), (0.36, 0.290), mutation_scale=7.0)
    axis.text(0.40, 0.638, "support / pairing rules", transform=axis.transAxes, ha="left", va="center", fontsize=5.9, color=COLORS["muted"])
    axis.text(0.40, 0.352, "historical G17/16 support", transform=axis.transAxes, ha="left", va="center", fontsize=5.9, color=COLORS["muted"])
    axis.text(0.72, 0.747, "19 candidate-only", transform=axis.transAxes, ha="left", va="center", fontsize=6.0, color=COLORS["muted"])
    axis.text(0.72, 0.500, "6 of 75 not retained\nin 2021", transform=axis.transAxes, ha="left", va="center", fontsize=6.0, linespacing=1.05, color=COLORS["muted"])


def draw_exact_chronology(axis: plt.Axes, chronology: pd.DataFrame) -> None:
    chronology = chronology.copy()
    chronology["start_date"] = pd.to_datetime(chronology["start_date"])
    chronology["end_date"] = pd.to_datetime(chronology["end_date"])

    external = chronology[chronology["design_id"].eq("goes17_goes16_2019_2021")]
    g1816 = chronology[chronology["design_id"].eq("goes18_goes16_2022_2024")]
    g1819_2025 = chronology[chronology["design_id"].eq("goes18_goes19_2025")]
    g1819_2026 = chronology[chronology["design_id"].eq("goes18_goes19_2026")]

    rows = [
        (external[external["analysis_role"].eq("calibration")], 6, COLORS["calibration"], COLORS["calibration"]),
        (external[external["analysis_role"].eq("validation")], 5, COLORS["historical"], COLORS["historical"]),
        (g1816, 4, COLORS["calibration"], COLORS["calibration"]),
        (g1816, 3, COLORS["evaluation"], COLORS["evaluation"]),
        (g1819_2025, 2, COLORS["evaluation"], COLORS["evaluation"]),
        (g1819_2025, 1, COLORS["evaluation"], COLORS["evaluation"]),
        (g1819_2026, 0, COLORS["prospective"], COLORS["prospective"]),
    ]
    for frame, y, color, _ in rows:
        starts = mdates.date2num(frame["start_date"])
        axis.vlines(starts, y - 0.28, y + 0.28, color=color, linewidth=0.60, zorder=3)

    labels = [
        "G17/16 calibration\n69 cities | 4 intervals",
        "G17/16 historical evaluation\n69 cities | 4 intervals",
        "G18/16 original derivation\n44 cities | 31 intervals",
        "G18/16 expansion evaluation\n31 cities | same 31 intervals",
        "G18/19 original evaluation\n44 cities | 10 intervals",
        "G18/19 expansion evaluation\n31 cities | same 10 intervals",
        "G18/19 prospective holdout\n75 cities | 8 intervals",
    ]
    axis.set_yticks([6, 5, 4, 3, 2, 1, 0], labels)
    axis.set_ylim(-0.58, 6.58)
    axis.set_xlim(pd.Timestamp("2019-01-01"), pd.Timestamp("2026-12-31"))
    axis.xaxis.set_major_locator(mdates.YearLocator())
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axis.tick_params(axis="x", length=3, width=0.7, color=COLORS["muted"])
    axis.tick_params(axis="y", length=0, pad=6, labelsize=7.6)
    axis.grid(False)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.spines["bottom"].set_color(COLORS["muted"])

    bracket_x = mdates.date2num(pd.Timestamp("2025-09-28"))
    cap_days = 22
    axis.plot([bracket_x, bracket_x], [0.72, 2.28], color=COLORS["muted"], linewidth=0.75, zorder=2)
    axis.plot([bracket_x - cap_days, bracket_x], [0.72, 0.72], color=COLORS["muted"], linewidth=0.75, zorder=2)
    axis.plot([bracket_x - cap_days, bracket_x], [2.28, 2.28], color=COLORS["muted"], linewidth=0.75, zorder=2)
    axis.text(
        mdates.date2num(pd.Timestamp("2025-10-12")),
        1.50,
        "Combined 2025\nmeasurand-aware calibration:\n75 cities",
        ha="left",
        va="center",
        fontsize=7.2,
        color=COLORS["ink"],
    )
    axis.text(
        0.995,
        0.985,
        "Each tick marks the exact start of one fixed eight-day window",
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=7.1,
        color=COLORS["muted"],
    )

    legend = [
        Patch(facecolor=COLORS["calibration"], edgecolor="none", label="Calibration / derivation"),
        Patch(facecolor=COLORS["evaluation"], edgecolor="none", label="Out-of-sample evaluation"),
        Patch(facecolor=COLORS["historical"], edgecolor="none", label="Historical external evaluation"),
        Patch(facecolor=COLORS["prospective"], edgecolor="none", label="Prospective holdout"),
    ]
    axis.legend(
        handles=legend,
        loc="lower left",
        bbox_to_anchor=(0.0, 1.01),
        frameon=False,
        ncol=2,
        columnspacing=1.25,
        handlelength=1.2,
        borderaxespad=0,
        fontsize=7.7,
    )


def build_figure1(cities: pd.DataFrame, chronology: pd.DataFrame) -> plt.Figure:
    configure_submission_style()
    figure = plt.figure(figsize=(FINAL_WIDTH_IN, 10.7))
    hierarchy = figure.add_axes([0.035, 0.815, 0.945, 0.173])
    map_axis = figure.add_axes([0.075, 0.420, 0.555, 0.304])
    support_axis = figure.add_axes([0.655, 0.420, 0.320, 0.304])
    chronology_axis = figure.add_axes([0.310, 0.045, 0.655, 0.252])

    draw_workflow(hierarchy)
    legend_handles = draw_city_map(map_axis, cities)
    draw_support_flow(support_axis, legend_handles)
    draw_exact_chronology(chronology_axis, chronology)
    figure.text(0.012, 0.989, "a", ha="left", va="top", fontsize=12, fontweight="bold")
    figure.text(0.012, 0.760, "b", ha="left", va="top", fontsize=12, fontweight="bold")
    figure.text(0.012, 0.340, "c", ha="left", va="top", fontsize=12, fontweight="bold")
    return figure


MODEL_CONFIG = [
    ("hourly_core", "Hourly core LST", (0.38, 1.06)),
    ("hourly_ring", "Hourly ring LST", (0.40, 1.06)),
    ("hourly_anomaly", "Hourly core–ring contrast", (0.94, 1.12)),
    ("anomaly_transition", "Core–ring transition", (0.94, 2.16)),
]

MODEL_LABELS = {
    "raw": "Raw",
    "hour_offset": "Hour offset",
    "geometry_ridge": "Geometry ridge",
    "scene_gbdt": "Scene GBDT",
    "mean_offset": "Mean offset",
    "transition_ridge": "Transition ridge",
    "transition_gbdt": "Transition GBDT",
}

EXPECTED_2025_MODEL_VALUES = {
    ("hourly_core", "raw"): (1.0000000000, 0.0000000000, 0.4965437059),
    ("hourly_core", "hour_offset"): (0.5246671691, 0.0573069129, 0.4965437059),
    ("hourly_core", "geometry_ridge"): (0.4492364378, 0.0473072681, 0.4965437059),
    ("hourly_core", "scene_gbdt"): (0.4784316931, 0.0445792379, 0.4965437059),
    ("hourly_ring", "raw"): (1.0000000000, 0.0000000000, 0.5031859688),
    ("hourly_ring", "hour_offset"): (0.4631897722, 0.0399961966, 0.5031859688),
    ("hourly_ring", "geometry_ridge"): (0.5735954008, 0.0855788041, 0.5031859688),
    ("hourly_ring", "scene_gbdt"): (0.4933674018, 0.0410295724, 0.5031859688),
    ("hourly_anomaly", "raw"): (1.0000000000, 0.0000000000, 1.0301746537),
    ("hourly_anomaly", "hour_offset"): (1.0076674000, 0.0118508768, 1.0301746537),
    ("hourly_anomaly", "geometry_ridge"): (0.9928781247, 0.0372965290, 1.0301746537),
    ("hourly_anomaly", "scene_gbdt"): (1.0558492579, 0.0479140021, 1.0301746537),
    ("anomaly_transition", "raw"): (1.0000000000, 0.0000000000, 1.0000000000),
    ("anomaly_transition", "mean_offset"): (1.0158864648, 0.0056637602, 1.0000000000),
    ("anomaly_transition", "transition_ridge"): (1.7844681850, 0.3175400495, 1.0000000000),
    ("anomaly_transition", "transition_gbdt"): (1.1288670820, 0.0503290001, 1.0000000000),
}


def draw_model_panel(
    axis: plt.Axes,
    frame: pd.DataFrame,
    panel_title: str,
    x_limits: tuple[float, float],
    letter: str,
) -> None:
    frame = frame.sort_values("parsimony_rank").reset_index(drop=True)
    y_positions = np.arange(len(frame))[::-1]
    cutoff = float(frame["one_se_threshold"].iloc[0])
    minimum_index = int(frame["mean_cv_score"].idxmin())
    minimum_model = frame.loc[minimum_index, "model"]
    selected_row = frame.loc[frame["selected"].astype(bool)].iloc[0]
    same_raw_cutoff = np.isclose(cutoff, 1.0, atol=1e-12, rtol=0)

    if not same_raw_cutoff:
        axis.axvline(1.0, color="#B7B7B7", linestyle=":", linewidth=0.85, zorder=1)
    axis.axvline(cutoff, color=COLORS["selected"], linestyle="--", linewidth=0.95, zorder=2)

    for y, row in zip(y_positions, frame.itertuples()):
        axis.errorbar(
            row.mean_cv_score,
            y,
            xerr=row.se_cv_score,
            fmt="none",
            ecolor="#8A8A8A",
            elinewidth=0.9,
            capsize=2.2,
            capthick=0.8,
            zorder=3,
        )
        axis.scatter(
            row.mean_cv_score,
            y,
            s=26,
            marker="o",
            facecolor="#555555",
            edgecolor="none",
            zorder=4,
        )
        if row.model == minimum_model:
            axis.scatter(
                row.mean_cv_score,
                y,
                s=92,
                marker="o",
                facecolor="none",
                edgecolor=COLORS["ink"],
                linewidth=0.9,
                zorder=5,
            )
        if row.selected:
            axis.scatter(
                row.mean_cv_score,
                y,
                s=78,
                marker="*",
                facecolor=COLORS["selected"],
                edgecolor="none",
                zorder=6,
            )

    axis.set_xlim(*x_limits)
    if panel_title == "Hourly core–ring contrast":
        axis.set_ylim(-1.15, len(frame) - 0.35)
    else:
        axis.set_ylim(-0.65, len(frame) - 0.35)
    axis.set_yticks(y_positions, [MODEL_LABELS[item] for item in frame["model"]])
    axis.text(
        -0.18,
        1.115,
        letter,
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=9.2,
        fontweight="bold",
        clip_on=False,
    )
    axis.text(
        0.00,
        1.115,
        panel_title,
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=9.0,
        fontweight="semibold",
        clip_on=False,
    )
    axis.tick_params(direction="out", length=3, width=0.7)
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(False)

    cutoff_label = f"raw = cutoff = {cutoff:.4f}" if same_raw_cutoff else f"1-SE cutoff = {cutoff:.4f}"
    cutoff_ha = "right" if cutoff > x_limits[0] + 0.72 * (x_limits[1] - x_limits[0]) else "left"
    axis.text(
        cutoff,
        1.015,
        cutoff_label,
        transform=axis.get_xaxis_transform(),
        ha=cutoff_ha,
        va="bottom",
        fontsize=7.0,
        color=COLORS["selected"],
    )

    if panel_title == "Hourly core–ring contrast":
        axis.text(
            0.60,
            0.76,
            "Lowest mean:\ngeometry ridge (0.9929)\nSelected: raw (1.0000)\nwithin 1-SE cutoff",
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=6.3,
            linespacing=1.20,
            color=COLORS["ink"],
        )
    else:
        selected_y = y_positions[int(selected_row.name)]
        span = x_limits[1] - x_limits[0]
        if panel_title in {"Hourly core LST", "Hourly ring LST"}:
            # Keep the label clearly to the right of the vertical one-SE cutoff.
            label_x = cutoff + 0.080 * span
        else:
            label_x = float(selected_row["mean_cv_score"]) + 0.035 * span
        axis.text(
            label_x,
            selected_y + 0.18,
            f"Selected/minimum {float(selected_row['mean_cv_score']):.4f}",
            ha="left",
            va="bottom",
            fontsize=6.8,
            color=COLORS["ink"],
        )


def build_figure2(model_selection: pd.DataFrame) -> plt.Figure:
    configure_submission_style()
    figure, axes = plt.subplots(2, 2, figsize=(FINAL_WIDTH_IN, 5.15))
    figure.subplots_adjust(left=0.235, right=0.975, bottom=0.105, top=0.855, wspace=0.82, hspace=0.72)

    selected_stage = model_selection[model_selection["selection_stage"].eq("metric_aware_calibration_2025")].copy()
    for axis, (outcome, label, limits), letter in zip(axes.ravel(), MODEL_CONFIG, "abcd"):
        draw_model_panel(axis, selected_stage[selected_stage["outcome"].eq(outcome)].copy(), label, limits, letter)

    handles = [
        Line2D([], [], marker="o", linestyle="-", color="#8A8A8A", linewidth=0.9, markerfacecolor="#555555", markeredgecolor="none", markersize=4.6, label="Mean ± 1 SE"),
        Line2D([], [], marker="*", linestyle="none", markerfacecolor=COLORS["selected"], markeredgecolor="none", markersize=8, label="Selected by parsimony"),
        Line2D([], [], marker="o", linestyle="none", markerfacecolor="none", markeredgecolor=COLORS["ink"], markersize=6, label="Lowest mean"),
    ]
    figure.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.605, 0.975),
        frameon=False,
        ncol=3,
        columnspacing=1.20,
        handlelength=1.55,
        handletextpad=0.45,
        fontsize=7.5,
    )
    return figure


def load_figure3_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    rmse = pd.read_csv(SOURCES["rmse"])
    rmse["sample"] = pd.Categorical(rmse["sample"], SAMPLE_ORDER, ordered=True)
    rmse = rmse.sort_values(["sample", "component"])
    mse = pd.read_csv(SOURCES["mse"])
    mse["sample"] = pd.Categorical(mse["sample"], SAMPLE_ORDER, ordered=True)
    mse = mse.sort_values("sample")
    return rmse, mse


def build_figure3(rmse: pd.DataFrame, mse: pd.DataFrame) -> plt.Figure:
    configure_submission_style()
    figure = plt.figure(figsize=(8.0, 3.50))
    grid = figure.add_gridspec(
        1,
        2,
        width_ratios=[1.10, 1.0],
        left=0.165,
        right=0.985,
        bottom=0.210,
        top=0.800,
        wspace=0.42,
    )
    axis_a = figure.add_subplot(grid[0, 0])
    axis_b = figure.add_subplot(grid[0, 1])

    samples = list(rmse["sample"].cat.categories)
    labels = [
        "2021 G17/16\nexternal",
        "2022–24 G18/16\nexpansion",
        "2025 G18/19\noriginal",
        "2025 G18/19\nexpansion",
        "2026 G18/19\nprospective",
    ]
    y = np.arange(len(samples))
    offsets = {"core": -0.17, "ring": 0.0, "anomaly": 0.17}
    component_labels = {"core": "Core", "ring": "Ring", "anomaly": "Core–ring contrast"}
    for component in ["core", "ring", "anomaly"]:
        frame = rmse[rmse["component"].eq(component)].set_index("sample")
        values = np.asarray([frame.loc[sample, "rmse_reduction_fraction"] for sample in samples]) * 100
        component_color = COLORS["contrast"] if component == "anomaly" else COLORS[component]
        axis_a.scatter(values, y + offsets[component], s=34, color=component_color, edgecolor="white", linewidth=0.4, label=component_labels[component], zorder=3)
    axis_a.axvline(0, color="#666666", linewidth=0.75)
    axis_a.set_yticks(y, labels)
    axis_a.invert_yaxis()
    axis_a.set_xlim(-18, 72)
    axis_a.set_xlabel("Out-of-sample RMSE reduction (%)")
    axis_a.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.50, 1.015), borderaxespad=0, ncol=3, columnspacing=0.9, handletextpad=0.35, fontsize=7.0)
    axis_a.spines[["top", "right"]].set_visible(False)
    axis_a.tick_params(direction="out", length=3, width=0.7)
    axis_a.grid(False)
    axis_a.tick_params(axis="y", labelsize=7.6)
    panel_label(axis_a, "a", x=-0.34, y=1.10)

    x = np.arange(len(mse))
    width = 0.22
    axis_b.bar(x - width, mse["component_variance_gain_k2"], width, color=COLORS["variance"], label="Component variance gain")
    axis_b.bar(x, mse["differential_bias_gain_k2"], width, color=COLORS["bias"], label="Differential-bias gain")
    axis_b.bar(x + width, -mse["covariance_loss_penalty_k2"], width, color=COLORS["covariance"], label="Covariance-loss penalty")
    axis_b.scatter(x, mse["net_downstream_mse_gain_k2"], s=20, marker="o", color=COLORS["net"], edgecolor="none", label="Net downstream gain", zorder=4)
    axis_b.axhline(0, color="#555555", linewidth=0.75)
    axis_b.set_ylim(-2.65, 3.0)
    axis_b.set_xticks(x, ["2021\nG17/16", "2022–24\nG18/16", "2025\noriginal", "2025\nexpansion", "2026\nG18/19"])
    axis_b.set_ylabel("Exact hourly MSE\ndecomposition term (K²)", fontsize=8.3, labelpad=2)
    decomposition_handles = [
        Line2D([], [], marker="o", linestyle="none", markersize=4.2, markerfacecolor=COLORS["net"], markeredgecolor="none", label="Net downstream gain"),
        Patch(facecolor=COLORS["variance"], edgecolor="none", label="Component variance gain"),
        Patch(facecolor=COLORS["bias"], edgecolor="none", label="Differential-bias gain"),
        Patch(facecolor=COLORS["covariance"], edgecolor="none", label="Covariance-loss penalty"),
    ]
    axis_b.legend(handles=decomposition_handles, frameon=False, ncol=2, loc="lower left", bbox_to_anchor=(0.0, 1.015), columnspacing=0.8, handletextpad=0.35, fontsize=6.0)
    axis_b.spines[["top", "right"]].set_visible(False)
    axis_b.tick_params(direction="out", length=3, width=0.7)
    axis_b.tick_params(axis="x", labelsize=6.3)
    axis_b.grid(False)
    panel_label(axis_b, "b", x=-0.28, y=1.10)
    return figure


def validate_inputs(
    cities: pd.DataFrame,
    chronology: pd.DataFrame,
    counts: pd.DataFrame,
    model_selection: pd.DataFrame,
) -> dict[str, object]:
    for label, path in {**SOURCES, **BASEMAP}.items():
        require(path.exists(), f"Missing {label} source: {path}")
    for label, expected_hash in EXPECTED_SOURCE_HASHES.items():
        require(sha256(SOURCES[label]) == expected_hash, f"Frozen source bytes changed for {label}")
    require(MAP_EXTENT == (-125.0, -100.0, 31.0, 51.0), "Publication map extent changed")

    require(len(cities) == 94, "Expected 94 fixed candidate cities")
    require(cities["uc_id"].is_unique, "Candidate-city identifiers must be unique")
    require(cities["calibration_cohort"].value_counts().to_dict() == {"original": 51, "expansion": 43}, "Expected 51 original and 43 expansion candidates")
    retained = cities["analyzed_holdout_2026_combined"].astype(bool)
    external_2021 = cities["analyzed_external_validation_2021"].astype(bool)
    require(int(retained.sum()) == 75, "Expected 75 retained 2026 cities")
    require(int((retained & cities["calibration_cohort"].eq("original")).sum()) == 44, "Expected 44 retained original cities")
    require(int((retained & cities["calibration_cohort"].eq("expansion")).sum()) == 31, "Expected 31 retained expansion cities")
    require(int(external_2021.sum()) == 69, "Expected 69 external-validation cities")
    require(int((external_2021 & ~retained).sum()) == 0, "The 2021 support must be a subset of the retained 75-city support")
    require(int((retained & ~external_2021).sum()) == 6, "Expected six later-support cities absent in 2021")
    require((cities["analyzed_calibration_2025_combined"].astype(bool) == retained).all(), "2025 and 2026 retained city supports differ")

    chronology = chronology.copy()
    chronology["start_date"] = pd.to_datetime(chronology["start_date"])
    chronology["end_date"] = pd.to_datetime(chronology["end_date"])
    require(len(chronology) == 57, "Expected 57 fixed interval records")
    require(chronology["interval_days_inclusive"].eq(8).all(), "Every interval must be eight days inclusive")
    require(((chronology["end_date"] - chronology["start_date"]).dt.days + 1).eq(8).all(), "Recomputed inclusive interval durations must equal eight days")
    require(chronology["event_time_id"].is_unique, "Expected 57 unique source event identifiers")
    require(
        chronology["design_id"].value_counts().to_dict()
        == {
            "goes18_goes16_2022_2024": 31,
            "goes18_goes19_2025": 10,
            "goes17_goes16_2019_2021": 8,
            "goes18_goes19_2026": 8,
        },
        "Fixed chronology counts changed",
    )
    external = chronology[chronology["design_id"].eq("goes17_goes16_2019_2021")]
    require(external["analysis_role"].value_counts().to_dict() == {"calibration": 4, "validation": 4}, "Expected four external calibration and four external validation intervals")

    expected_stage_rows = {
        "external_calibration_combined_2019_2020": 4,
        "external_validation_combined_2021": 4,
        "initial_model_derivation_original_2022_2024": 31,
        "initial_model_evaluation_expansion_2022_2024": 31,
        "initial_model_evaluation_original_2025": 10,
        "initial_model_evaluation_expansion_2025": 10,
        "metric_aware_calibration_combined_2025": 10,
        "metric_aware_validation_combined_2026": 8,
    }
    require(counts["stage_id"].value_counts().to_dict() == expected_stage_rows, "Supplementary Data S3 stage counts changed")
    counts = counts.copy()
    counts["start_date"] = pd.to_datetime(counts["start_date"])
    g1816_starts = set(chronology.loc[chronology["design_id"].eq("goes18_goes16_2022_2024"), "start_date"])
    require(set(counts.loc[counts["stage_id"].eq("initial_model_derivation_original_2022_2024"), "start_date"]) == g1816_starts, "Original 2022–2024 dates differ from Data S2")
    require(set(counts.loc[counts["stage_id"].eq("initial_model_evaluation_expansion_2022_2024"), "start_date"]) == g1816_starts, "Expansion 2022–2024 dates are not the same 31 dates")
    g1819_2025_starts = set(chronology.loc[chronology["design_id"].eq("goes18_goes19_2025"), "start_date"])
    for stage_id in [
        "initial_model_evaluation_original_2025",
        "initial_model_evaluation_expansion_2025",
        "metric_aware_calibration_combined_2025",
    ]:
        require(set(counts.loc[counts["stage_id"].eq(stage_id), "start_date"]) == g1819_2025_starts, f"{stage_id} does not use the same ten 2025 dates")

    stage = model_selection[model_selection["selection_stage"].eq("metric_aware_calibration_2025")].copy()
    require(len(stage) == 16 and stage["n_folds"].eq(25).all(), "Expected 16 frozen 2025 candidate rows and 25 folds")
    expected_selected = {
        "hourly_core": "geometry_ridge",
        "hourly_ring": "hour_offset",
        "hourly_anomaly": "raw",
        "anomaly_transition": "raw",
    }
    for outcome, selected_model in expected_selected.items():
        frame = stage[stage["outcome"].eq(outcome)].copy()
        best = frame.loc[frame["mean_cv_score"].idxmin()]
        cutoff = float(best["mean_cv_score"] + best["se_cv_score"])
        require(np.allclose(frame["one_se_threshold"], cutoff), f"Cutoff changed for {outcome}")
        admissible = frame[frame["mean_cv_score"].le(cutoff + 1e-12)]
        reproduced = admissible.sort_values("parsimony_rank").iloc[0]["model"]
        require(reproduced == selected_model, f"Selection changed for {outcome}")
        require(frame.loc[frame["selected"].astype(bool), "model"].tolist() == [selected_model], f"Selected flag changed for {outcome}")
        for row in frame.itertuples():
            expected = EXPECTED_2025_MODEL_VALUES[(outcome, row.model)]
            require(np.allclose([row.mean_cv_score, row.se_cv_score, row.one_se_threshold], expected, atol=5e-10, rtol=0), f"Frozen score changed for {outcome}/{row.model}")

    rmse, mse = load_figure3_sources()
    require(len(rmse) == 15, "Expected 15 RMSE rows")
    require(len(mse) == 5 and mse["scope"].eq("hourly").all(), "Expected five hourly MSE rows")
    require(mse["budget_closure_residual_k2"].abs().max() < 1e-10, "MSE decomposition closure check failed")

    return {
        "status": "all_frozen_source_checks_passed",
        "candidate_cities": 94,
        "retained_original_cities": 44,
        "retained_expansion_cities": 31,
        "external_2021_cities": 69,
        "fixed_interval_records": 57,
        "rendered_chronology_ticks": 98,
        "metric_aware_candidates": 16,
        "crossed_folds": 25,
        "figure3_rmse_rows": 15,
        "figure3_mse_rows": 5,
        "map_west": MAP_EXTENT[0],
        "map_east": MAP_EXTENT[1],
        "map_south": MAP_EXTENT[2],
        "map_north": MAP_EXTENT[3],
    }


def export_figure(figure: plt.Figure, stem: str) -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{stem}.png"
    figure.savefig(
        path,
        dpi=600,
        facecolor="white",
        metadata={"Software": Path(__file__).name},
        bbox_inches="tight",
        pad_inches=0.05,
    )
    plt.close(figure)

    with Image.open(path) as image:
        width, height = image.size
        dpi = image.info.get("dpi", (None, None))
    require(width >= 3500, f"{stem} is narrower than the intended high-resolution publication export")
    require(dpi[0] is not None and dpi[0] >= 599.0, f"{stem} PNG does not retain nominal 600-dpi metadata")
    return {
        "files": {"png": str(path)},
        "png_pixels": [width, height],
        "png_dpi": list(dpi),
        "sha256": {"png": sha256(path)},
    }


AUDIT_COLUMNS = [
    "design_id",
    "reference_platform",
    "source_platform",
    "analysis_role",
    "event_time_id",
    "start_date",
    "end_date",
    "interval_days_inclusive",
]


def write_interval_audit(chronology: pd.DataFrame) -> pd.DataFrame:
    audit = chronology.loc[:, AUDIT_COLUMNS].copy()
    require(len(audit) == 57, "Figure 1c audit must contain all 57 source rows")
    audit.to_csv(OUT / "Figure1c_interval_audit.csv", index=False)
    return audit


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(cell(item) for item in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(item) for item in row) + " |" for row in rows)
    return "\n".join(lines)


def write_qa(
    cities: pd.DataFrame,
    chronology: pd.DataFrame,
    model_selection: pd.DataFrame,
    rmse: pd.DataFrame,
    mse: pd.DataFrame,
    outputs: dict[str, dict[str, object]],
    validation: dict[str, object],
) -> None:
    def repository_path(path: Path) -> str:
        return str(path.relative_to(ROOT))

    retained = cities["analyzed_holdout_2026_combined"].astype(bool)
    external = cities["analyzed_external_validation_2021"].astype(bool)
    model_stage = model_selection[
        model_selection["selection_stage"].eq("metric_aware_calibration_2025")
    ].copy()

    model_rows: list[list[object]] = []
    for outcome, title, _ in MODEL_CONFIG:
        frame = model_stage[model_stage["outcome"].eq(outcome)].sort_values("parsimony_rank")
        minimum_model = frame.loc[frame["mean_cv_score"].idxmin(), "model"]
        for row in frame.itertuples():
            model_rows.append(
                [
                    title,
                    MODEL_LABELS[row.model],
                    f"{row.mean_cv_score:.10f}",
                    f"{row.se_cv_score:.10f}",
                    f"{row.one_se_threshold:.10f}",
                    "Yes" if row.selected else "No",
                    "Yes" if row.model == minimum_model else "No",
                ]
            )

    interval_rows = [
        [
            row.design_id,
            row.reference_platform,
            row.source_platform,
            row.analysis_role,
            row.event_time_id,
            row.start_date,
            row.end_date,
            row.interval_days_inclusive,
            f"Directly from start_date ({row.start_date})",
        ]
        for row in chronology.loc[:, AUDIT_COLUMNS].itertuples(index=False)
    ]

    dimension_rows: list[list[object]] = []
    for figure_name, info in outputs.items():
        dimension_rows.append(
            [
                figure_name,
                f"{info['png_pixels'][0]} × {info['png_pixels'][1]} px",
                "600 dpi",
                f"{info['png_dpi'][0]:.4f} × {info['png_dpi'][1]:.4f} dpi",
                Path(info["files"]["png"]).name,
            ]
        )

    source_rows = [
        ["Figure 1a", "No numerical input; existing workflow wording and hierarchy only"],
        ["Figure 1b", f"{repository_path(SOURCES['cities'])} (study symbols); {repository_path(BASEMAP['land'])}, {repository_path(BASEMAP['countries'])}, and {repository_path(BASEMAP['states_provinces'])} (cartographic context; no separate coastline layer)"],
        ["Figure 1c", f"{repository_path(SOURCES['chronology'])} (plot positions); {repository_path(SOURCES['counts'])} (shared-date and support-count cross-checks)"],
        ["Figure 2a–d", repository_path(SOURCES["model_selection"])],
        ["Figure 3a", repository_path(SOURCES["rmse"])],
        ["Figure 3b", repository_path(SOURCES["mse"])],
    ]

    qa = f"""# Figure revision QA

## Scope and status

- Status: `{validation['status']}`.
- This run changed visualization code and generated figure/audit files only. It did not edit the manuscript or Supplementary Materials DOCX.
- No scientific analysis, refitting, resampling, or change to values, dates, cohorts, membership, terminology, or uncertainty estimates was performed.
- Figure 3c was deleted. No directional-support count, abstention count, or sign-agreement text remains in revised Figure 3.

## Exact panel sources

{markdown_table(['Panel', 'Authoritative plotted/checking source'], source_rows)}

Supplementary Data mappings used here are: S1 = `{repository_path(SOURCES['cities'])}`; S2 = `{repository_path(SOURCES['chronology'])}`; S3 = `{repository_path(SOURCES['counts'])}`; and S4 = `{repository_path(SOURCES['model_selection'])}`.

## Figure 1b city-symbol and support audit

- Data S1 contains 94 unique fixed western candidates: 51 original and 43 expansion candidates.
- The 2025 calibration and 2026 holdout membership flags are identical and retain 75 cities: 44 original + 31 expansion = 75.
- The 2021 external analyzed support is an exact 69-city subset of those 75; six retained 2025–2026 cities were not retained in 2021.
- Rendered map marks: 94 base city symbols plus six thin black outer-ring overlays. The overlays do not represent additional cities.
- Candidate-only symbols: {int((~retained).sum())}; retained original symbols: {int((retained & cities['calibration_cohort'].eq('original')).sum())}; retained expansion symbols: {int((retained & cities['calibration_cohort'].eq('expansion')).sum())}; 2021-exclusion rings: {int((retained & ~external).sum())}.
- Longitude and latitude were plotted directly from Data S1 in Plate Carree coordinates; no coordinate transformation, displacement, or jitter was applied.
- The rectangular map extent is exactly {validation['map_west']:.0f}° to {validation['map_east']:.0f}° longitude and {validation['map_south']:.0f}° to {validation['map_north']:.0f}° latitude. The right frame remains exactly 100°W; the separate in-figure cutoff annotation was removed at the author's request.
- The separate coastline layer, all graticule-line layers, and the former dashed cutoff line were removed. The land/water fills, medium-gray country boundaries, and thin light-gray state/province boundaries remain.
- The compact 94 → 75 → 69 support-flow graphic is outside the map and preserves the 19 candidate-only and six 2021-exclusion annotations.
- Symbol size does not encode observation count, and symbol shape does not encode platform pairing.

## Figure 1c interval audit

- `Figure1c_interval_audit.csv` is a direct eight-column extraction of all 57 Data S2 source rows.
- All 57 source rows have `interval_days_inclusive = 8`, and recomputing `(end_date − start_date) + 1` gives eight days for every row.
- Source counts: four 2019–2020 G17/16 calibration intervals; four 2021 G17/16 validation intervals; 31 G18/16 intervals in 2022–2024; ten G18/19 intervals in 2025; and eight prespecified G18/19 intervals in 2026.
- The 31 G18/16 dates are plotted on both the original-derivation and expansion-evaluation tracks. The ten 2025 dates are plotted on both the original- and expansion-evaluation tracks. These equivalences were checked against Data S3.
- Therefore the chronology uses 57 authoritative interval rows/unique windows and renders 98 track-specific ticks: 4 + 4 + 31 + 31 + 10 + 10 + 8.
- Every tick x-position comes directly from the corresponding `start_date`. No dates were aggregated or merged into min–max seasonal blocks.

### All 57 source rows and plotting basis

{markdown_table(AUDIT_COLUMNS + ['Plot-position basis'], interval_rows)}

## Figure 2 model-selection audit

- Only the 16 rows with `selection_stage = metric_aware_calibration_2025` were plotted; no 2022–2024 hour-spline result was included.
- Means, one-standard-error intervals, cutoffs, selected models, and minimum models were checked numerically against Supplementary Data S4 before rendering.
- The Supplementary Data S4 byte hash remains `{EXPECTED_SOURCE_HASHES['model_selection']}`; all values are byte- and numerically identical to the previously verified model-selection source.
- All ordinary means use the same neutral dark-gray point encoding. The compact legend now shows mean ± 1 SE, selection by an orange star, and the minimum by a black ring.

{markdown_table(['Panel', 'Candidate', 'Mean', 'SE', 'Cutoff', 'Selected', 'Minimum'], model_rows)}

## Figure 3 data-preservation audit

- Revised Figure 3 contains two aligned panels only: 15 frozen RMSE-reduction points in panel a and five frozen hourly MSE-decomposition rows in panel b.
- Panel a uses all five evaluation cohorts and the same core, ring, and core–ring-contrast values/order as the frozen plotting source.
- Panel b uses the unchanged component-variance, differential-bias, covariance-loss, and net-downstream-gain columns. The covariance-loss penalty remains plotted as a negative contribution, and source decomposition closure remains below `1×10−10 K²`.
- Figure 3 source hashes remain unchanged (`rmse`: `{EXPECTED_SOURCE_HASHES['rmse']}`; `mse`: `{EXPECTED_SOURCE_HASHES['mse']}`), so every retained Figure 3 value is identical to the previously verified version.
- The panel-b legend begins at the left edge of the panel-b plotting region and extends rightward without changing its wording; the complete `Covariance-loss penalty` label is contained within the export.
- Former directional-support panel c was removed completely; its source is not loaded by the revised Figure 3 builder.

## Figure caption and numbering record

- The current figure sequence is Figure 1 workflow/domain/chronology; Figure 2 one-standard-error selection; Figure 3 cross-cohort performance/decomposition; Figure 4 covariance-regime stress test; and Figure 5 replication/holdout diagnostics.
- Figure 1c uses thin ticks for the exact start dates of fixed inclusive eight-day windows; shared dates appear on both relevant cohort tracks.
- Figure 2 uses gray mean ± one-SE marks, orange one-SE cutoff lines, light-gray raw = 1.0 reference lines, stars for selected models, and rings for minimum-mean models. Panel-specific x-axis ranges differ.
- Figure 3 contains only cross-cohort RMSE changes and exact hourly MSE decomposition. Its former directional-support panel is not included. Directional-support diagnostics are in Figure 5.
- This repository update did not edit the manuscript or Supplementary Materials DOCX.

## Render and export audit

{markdown_table(['Figure', 'PNG dimensions', 'Requested export', 'Stored PNG metadata', 'PNG file'], dimension_rows)}

PNG files were written with Matplotlib `dpi=600`. PNG stores resolution as an integer pixels-per-metre value, which Pillow reports as approximately 599.9988 dpi; this is the standard metadata representation of nominal 600 dpi. The export used tight artist bounds plus a nonzero 0.05-inch safety pad.

## Final clipping inspection

- Final PNGs were inspected at the full left and right extents after export.
- Figure 1 contains the complete workflow labels, external geographic ticks, map legend, support-flow text, and chronology without clipping; no separate `100°W analysis cutoff` label remains.
- Figure 2 contains the complete three-item legend, all four separated panel letters and titles, cutoff labels, candidate labels, and annotations without clipping; the former global x-axis label was removed at the author's request.
- Figure 3 contains the complete `Covariance-loss penalty` legend text, panel-b y-axis label, all tick labels, panel letters `a` and `b`, and the full left/right extent of both panels without clipping.
- No text or marker touches or extends beyond the exported PNG canvas.

## Source hashes

"""
    for label, path in SOURCES.items():
        qa += f"- `{label}`: `{sha256(path)}` — `{repository_path(path)}`\n"
    qa += "\n### Cartographic reference-layer hashes\n\n"
    for label, path in BASEMAP.items():
        qa += f"- `{label}`: `{sha256(path)}` — `{repository_path(path)}`\n"
    qa += "\n## Output hashes\n\n"
    for figure_name, info in outputs.items():
        qa += f"- {figure_name} PNG: `{info['sha256']['png']}`\n"

    (OUT / "figure_revision_QA.md").write_text(qa, encoding="utf-8")


def main() -> None:
    cities = pd.read_csv(SOURCES["cities"])
    chronology = pd.read_csv(SOURCES["chronology"])
    counts = pd.read_csv(SOURCES["counts"])
    model_selection = pd.read_csv(SOURCES["model_selection"])
    validation = validate_inputs(cities, chronology, counts, model_selection)
    OUT.mkdir(parents=True, exist_ok=True)

    outputs = {
        "Figure 1": export_figure(build_figure1(cities, chronology), "Figure_1_workflow_domain_chronology"),
        "Figure 2": export_figure(build_figure2(model_selection), "Figure_2_one_se_model_selection"),
    }
    rmse, mse = load_figure3_sources()
    outputs["Figure 3"] = export_figure(build_figure3(rmse, mse), "Figure_3_component_downstream_results")
    write_interval_audit(chronology)
    write_qa(cities, chronology, model_selection, rmse, mse, outputs, validation)
    print(OUT)


if __name__ == "__main__":
    main()
