"""
resin_page.py

Resin Analysis page for the Dash app.

Provides five chart types for exploring resin dispense data:
  1. Part Count       -- bar chart of dispense counts by part number
  2. Resin Weight     -- boxplot of total_weight_lbs by part number with
                         nominal reference lines
  3. Overshoot        -- scatter / aggregated line of resin_overshoot_lbs
                         over time
  4. Extra Resin      -- % of dispenses using extra resin by part number,
                         with median extra weight annotated
  5. Resin Use by Time -- average total_weight_lbs by hour of day or month

Import in app.py and call register_callbacks(app).
Add "Resin Analysis" / "/resin-analysis" to nav.py PAGES.
"""

import datetime as dt
import io

import pandas as pd
import numpy as np
import plotly.graph_objects as go

import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc

from analytics import get_connection
from nav import navbar

import yaml

CONFIG_FILE = "config_vars.yaml"

with open(CONFIG_FILE, "r") as f:
    config_data = yaml.safe_load(f)
    DB_PATH = config_data["db_path"]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RESIN_STATIONS = ["Gray Resin", "Tan Resin"]

# Colours that feel appropriate for gray and tan resin
RESIN_COLORS = {
    "Gray Resin": "#64748b",
    "Tan Resin":  "#b45309",
}

CHART_TYPES = [
    {"label": "Part Count",          "value": "part_count"},
    {"label": "Resin Weight by Part", "value": "resin_weight"},
    {"label": "Overshoot Over Time",  "value": "overshoot"},
    {"label": "Extra Resin Usage",    "value": "extra_resin"},
    {"label": "Resin Use by Time",    "value": "resin_by_time"},
]

AGGREGATION_LEVELS = [
    {"label": "Raw (every dispense)", "value": "raw"},
    {"label": "Hourly",               "value": "H"},
    {"label": "Daily",                "value": "D"},
    {"label": "Weekly",               "value": "W"},
    {"label": "Monthly",              "value": "ME"},
    {"label": "Yearly",               "value": "YE"},
]

TIME_BREAKDOWN = [
    {"label": "Hour of Day",   "value": "hour"},
    {"label": "Month of Year", "value": "month"},
]

# ---------------------------------------------------------------------------
# Shared styles (match app.py)
# ---------------------------------------------------------------------------

LABEL = {
    "fontSize": "11px", "fontWeight": "600", "color": "#475569",
    "letterSpacing": "0.06em", "textTransform": "uppercase",
    "marginBottom": "6px", "display": "block",
}

PANEL = {
    "backgroundColor": "#ffffff",
    "border": "1px solid #e2e8f0",
    "borderRadius": "8px",
    "padding": "16px",
    "marginBottom": "12px",
}

INPUT_STYLE = {
    "width": "100%", "padding": "7px 10px",
    "fontFamily": "Inter, sans-serif", "fontSize": "13px",
    "color": "#1e293b", "backgroundColor": "#ffffff",
    "border": "1px solid #cbd5e1", "borderRadius": "6px",
    "outline": "none",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_resin_data(
    db_path: str,
    resin_names: list,
    date_start: str = None,
    date_end: str = None,
) -> pd.DataFrame:
    """
    Load raw_resin_data for the given stations and date range.
    Combines first_part_number and second_part_number into a tidy
    'part_number' column for per-part analysis, and adds derived columns.
    """
    placeholders = ",".join("?" * len(resin_names))
    params = list(resin_names)

    clauses = [f"resin_name IN ({placeholders})"]
    if date_start:
        clauses.append("record_timestamp >= ?")
        params.append(date_start)
    if date_end:
        end_dt = (dt.date.fromisoformat(date_end)
                  + dt.timedelta(days=1)).isoformat()
        clauses.append("record_timestamp < ?")
        params.append(end_dt)

    where = "WHERE " + " AND ".join(clauses)

    conn = get_connection(db_path, read_only=True)
    df = pd.read_sql(f"""
        SELECT
            id,
            resin_name,
            record_timestamp,
            first_part_number,
            second_part_number,
            nominal_resin_weight_lbs,
            total_weight_lbs,
            resin_weight_lbs,
            pigment_weight_lbs,
            catalyst_weight_lbs,
            resin_overshoot_lbs,
            extra_resin_weight_lbs,
            extra_resin_start_weight_lbs,
            short_flag
        FROM raw_resin_data
        {where}
        ORDER BY record_timestamp ASC
    """, conn, params=params)
    conn.close()

    if df.empty:
        return df

    df["record_timestamp"] = pd.to_datetime(
        df["record_timestamp"], format="ISO8601"
    )
    df["hour"]  = df["record_timestamp"].dt.hour
    df["month"] = df["record_timestamp"].dt.month
    df["month_name"] = df["record_timestamp"].dt.strftime("%b")
    df["used_extra"] = (
        df["extra_resin_weight_lbs"].fillna(0) > 0
    ).astype(int)

    # Normalise part numbers to int strings, dropping 0 / null
    df["first_part_number"]  = df["first_part_number"].fillna(0).astype(int)
    df["second_part_number"] = df["second_part_number"].fillna(0).astype(int)

    return df


def _part_label(n: int) -> str:
    return f"P{n}"


# ---------------------------------------------------------------------------
# Plot builders
# ---------------------------------------------------------------------------

def _empty_fig(msg="Set filters and click Run"):
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=msg, font=dict(size=14, color="#64748b")),
        paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc", height=500,
    )
    return fig


def _base_layout(title_text, xaxis_title, yaxis_title):
    return dict(
        title=dict(text=title_text, font=dict(size=15, color="#1e293b"), x=0),
        xaxis=dict(title=xaxis_title, gridcolor="#e2e8f0",
                   color="#475569", zeroline=False),
        yaxis=dict(title=yaxis_title, gridcolor="#e2e8f0",
                   color="#475569", zeroline=False),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#1e293b", family="Inter, sans-serif"),
        legend=dict(bgcolor="#ffffff", bordercolor="#e2e8f0", borderwidth=1),
        margin=dict(l=60, r=20, t=60, b=80),
        height=500,
    )


# ── 1. Part Count ────────────────────────────────────────────────────────────

def build_part_count(df: pd.DataFrame, resin_names: list,
                     sort_by: str = "count") -> go.Figure:
    if df.empty:
        return _empty_fig("No data for the selected filters.")

    fig = go.Figure()

    # Build combined counts across all stations first so sort order is global
    all_first  = df[df["first_part_number"]  != 0]["first_part_number"]
    all_second = df[df["second_part_number"] != 0]["second_part_number"]
    global_counts = (
        pd.concat([all_first, all_second])
        .value_counts()
        .reset_index()
        .rename(columns={0: "count", "index": "part"})
    )
    global_counts.columns = ["part", "count"]

    if sort_by == "part":
        ordered_parts = sorted(global_counts["part"].tolist())
    else:  # "count" — descending, so ascending=True for horizontal bar
        global_counts = global_counts.sort_values("count", ascending=True)
        ordered_parts = global_counts["part"].tolist()

    for station in resin_names:
        sub = df[df["resin_name"] == station]
        if sub.empty:
            continue
        first_counts  = sub[sub["first_part_number"]  != 0]["first_part_number"].value_counts()
        second_counts = sub[sub["second_part_number"] != 0]["second_part_number"].value_counts()
        combined = first_counts.add(second_counts, fill_value=0).astype(int)

        # Align to global sort order
        x_vals = [int(combined.get(p, 0)) for p in ordered_parts]
        y_vals = [_part_label(p) for p in ordered_parts]

        fig.add_trace(go.Bar(
            x=x_vals,
            y=y_vals,
            orientation="h",
            name=station,
            marker_color=RESIN_COLORS.get(station, "#64748b"),
            opacity=0.85,
        ))

    fig.update_layout(
        **_base_layout("Part Count by Part Number", "Dispense Count", "Part Number"),
        barmode="group",
    )
    return fig


def _part_count_stats(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    rows = []
    for station in df["resin_name"].unique():
        sub = df[df["resin_name"] == station]
        first  = sub[sub["first_part_number"]  != 0]["first_part_number"]
        second = sub[sub["second_part_number"] != 0]["second_part_number"]
        combined = pd.concat([first, second]).value_counts()
        for part, count in combined.items():
            rows.append({
                "Station": station,
                "Part Number": _part_label(part),
                "Count": int(count),
                "% of Station Total": round(100 * count / len(sub), 1),
            })
    return sorted(rows, key=lambda r: r["Count"], reverse=True)


# ── 2. Resin Weight by Part ──────────────────────────────────────────────────

def build_resin_weight(df: pd.DataFrame, resin_names: list) -> go.Figure:
    if df.empty:
        return _empty_fig("No data for the selected filters.")

    plot_df = df[df["first_part_number"] != 0].copy()
    if plot_df.empty:
        return _empty_fig("No data with valid part numbers.")

    # Sort parts numerically for consistent x-axis order
    all_parts = sorted(plot_df["first_part_number"].unique())
    category_array = [_part_label(p) for p in all_parts]

    fig = go.Figure()

    for station in resin_names:
        sub = plot_df[plot_df["resin_name"] == station]
        if sub.empty:
            continue
        color = RESIN_COLORS.get(station, "#64748b")
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

        fig.add_trace(go.Box(
            x=[_part_label(p) for p in sub["first_part_number"]],
            y=sub["total_weight_lbs"],
            name=station,
            marker=dict(color=color, size=4, opacity=0.5),
            line=dict(color=color, width=2),
            fillcolor=f"rgba({r},{g},{b},0.15)",
            boxpoints="outliers",
        ))

    # Nominal reference — scatter trace with diamond markers, one per part
    nominals = (
        plot_df.groupby("first_part_number")["nominal_resin_weight_lbs"]
        .median()
    )
    fig.add_trace(go.Scatter(
        x=[_part_label(p) for p in nominals.index],
        y=nominals.values,
        mode="markers",
        name="Nominal",
        marker=dict(
            symbol="diamond",
            color="#dc2626",
            size=10,
            line=dict(color="#991b1b", width=1),
        ),
        hovertemplate="Part: %{x}<br>Nominal: %{y:.2f} lbs<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="Resin Dispensed by Part Number",
            font=dict(size=15, color="#1e293b"), x=0,
        ),
        xaxis=dict(
            title="Part Number",
            categoryorder="array",
            categoryarray=category_array,
            type="category",
            tickvals=category_array,
            ticktext=[str(p) for p in all_parts],
            gridcolor="#e2e8f0",
            color="#475569",
        ),
        yaxis=dict(
            title="Total Weight (lbs)",
            gridcolor="#e2e8f0",
            color="#475569",
            zeroline=False,
        ),
        boxmode="group",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#1e293b", family="Inter, sans-serif"),
        legend=dict(bgcolor="#ffffff", bordercolor="#e2e8f0", borderwidth=1),
        margin=dict(l=60, r=20, t=60, b=80),
        height=500,
    )
    return fig


def _resin_weight_stats(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    plot_df = df[df["first_part_number"] != 0].copy()
    rows = []
    for (part, station), g in plot_df.groupby(
        ["first_part_number", "resin_name"]
    ):
        vals = g["total_weight_lbs"].dropna()
        nom  = g["nominal_resin_weight_lbs"].median()
        if len(vals) == 0:
            continue
        rows.append({
            "Part Number": _part_label(part),
            "Station":     station,
            "N":           len(vals),
            "Nominal (lbs)": round(nom, 2),
            "Median (lbs)":  round(vals.median(), 2),
            "Mean (lbs)":    round(vals.mean(), 2),
            "Std Dev":       round(vals.std(), 2),
            "Min (lbs)":     round(vals.min(), 2),
            "Max (lbs)":     round(vals.max(), 2),
        })
    return sorted(rows, key=lambda r: r["Part Number"])


# ── 3. Overshoot Over Time ───────────────────────────────────────────────────

def build_overshoot(df: pd.DataFrame, resin_names: list,
                    aggr: str = "D") -> go.Figure:
    if df.empty:
        return _empty_fig("No data for the selected filters.")

    fig = go.Figure()

    aggr_label = next(
        (o["label"] for o in AGGREGATION_LEVELS if o["value"] == aggr), aggr
    )

    for station in resin_names:
        sub = df[df["resin_name"] == station].copy()
        if sub.empty:
            continue
        color = RESIN_COLORS.get(station, "#64748b")
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

        if aggr == "raw":
            fig.add_trace(go.Scatter(
                x=sub["record_timestamp"],
                y=sub["resin_overshoot_lbs"],
                mode="markers",
                name=station,
                marker=dict(color=color, size=5, opacity=0.4),
            ))
        else:
            grouped = sub.set_index("record_timestamp")["resin_overshoot_lbs"].resample(aggr)
            agg = grouped.agg(["mean", "std", "min", "max"]).dropna(subset=["mean"]).reset_index()
            agg["std"] = agg["std"].fillna(0)
            agg["upper"] = agg["mean"] + agg["std"]
            agg["lower"] = agg["mean"] - agg["std"]

            # Filled ±1 std dev band
            fig.add_trace(go.Scatter(
                x=pd.concat([agg["record_timestamp"], agg["record_timestamp"].iloc[::-1]]),
                y=pd.concat([agg["upper"], agg["lower"].iloc[::-1]]),
                fill="toself",
                fillcolor=f"rgba({r},{g},{b},0.12)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip",
                name=f"{station} ±1σ",
            ))

            # Mean line
            fig.add_trace(go.Scatter(
                x=agg["record_timestamp"],
                y=agg["mean"],
                mode="lines+markers",
                name=station,
                line=dict(color=color, width=2),
                marker=dict(color=color, size=5),
                hovertemplate=(
                    "%{x}<br>"
                    "Mean overshoot: %{y:.3f} lbs<br>"
                    "<extra></extra>"
                ),
            ))

    # Zero reference line
    fig.add_hline(y=0, line_dash="dash", line_color="#94a3b8", line_width=1)

    fig.update_layout(
        **_base_layout(
            f"Resin Overshoot Over Time — Mean ± 1σ ({aggr_label})",
            "Date",
            "Overshoot (lbs)",
        ),
        xaxis_type="date",
        annotations=[dict(
            text="Overshoot = machine dispensing error (not intentional extra resin). "
                 "Positive = over target, negative = under target.",
            xref="paper", yref="paper",
            x=0, y=-0.18,
            showarrow=False,
            font=dict(size=11, color="#64748b"),
            align="left",
        )],
    )
    return fig


def _overshoot_stats(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    rows = []
    for station in df["resin_name"].unique():
        vals = df[df["resin_name"] == station]["resin_overshoot_lbs"].dropna()
        if len(vals) == 0:
            continue
        rows.append({
            "Station":      station,
            "N":            len(vals),
            "Mean (lbs)":   round(vals.mean(), 3),
            "Median (lbs)": round(vals.median(), 3),
            "Std Dev":      round(vals.std(), 3),
            "Min (lbs)":    round(vals.min(), 3),
            "Max (lbs)":    round(vals.max(), 3),
            "% Positive":   round(100 * (vals > 0).mean(), 1),
            "% Negative":   round(100 * (vals < 0).mean(), 1),
        })
    return rows


# ── 4. Extra Resin Usage ─────────────────────────────────────────────────────

def build_extra_resin(df: pd.DataFrame, resin_names: list) -> go.Figure:
    if df.empty:
        return _empty_fig("No data for the selected filters.")

    plot_df = df[df["first_part_number"] != 0].copy()
    if plot_df.empty:
        return _empty_fig("No data with valid part numbers.")

    fig = go.Figure()

    for station in resin_names:
        sub = plot_df[plot_df["resin_name"] == station]
        if sub.empty:
            continue
        color = RESIN_COLORS.get(station, "#64748b")

        stats = (
            sub.groupby("first_part_number")
            .agg(
                total=("id", "count"),
                extra_count=("used_extra", "sum"),
                median_extra=("extra_resin_weight_lbs", lambda x:
                              x[x > 0].median() if (x > 0).any() else 0),
            )
            .reset_index()
        )
        stats["pct_extra"] = 100 * stats["extra_count"] / stats["total"]
        stats = stats.sort_values("pct_extra", ascending=True)

        fig.add_trace(go.Bar(
            x=stats["pct_extra"],
            y=[_part_label(p) for p in stats["first_part_number"]],
            orientation="h",
            name=station,
            marker_color=color,
            opacity=0.85,
            text=[
                f"{pct:.1f}%  (med extra: {med:.2f} lbs)"
                if med > 0 else f"{pct:.1f}%"
                for pct, med in zip(
                    stats["pct_extra"], stats["median_extra"]
                )
            ],
            textposition="outside",
            hovertemplate=(
                "Part: %{y}<br>"
                "% with extra resin: %{x:.1f}%<br>"
                "<extra></extra>"
            ),
        ))

    layout = _base_layout(
        "Extra Resin Usage by Part Number",
        "% of Dispenses Using Extra Resin",
        "Part Number",
    )
    # Override xaxis range — can't pass xaxis twice so update the dict
    layout["xaxis"] = dict(
        title="% of Dispenses Using Extra Resin",
        gridcolor="#e2e8f0",
        color="#475569",
        zeroline=False,
        range=[0, 115],
    )
    fig.update_layout(**layout, barmode="group")
    return fig


def _extra_resin_stats(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    plot_df = df[df["first_part_number"] != 0].copy()
    rows = []
    for (part, station), g in plot_df.groupby(
        ["first_part_number", "resin_name"]
    ):
        total      = len(g)
        used       = g["used_extra"].sum()
        extra_vals = g.loc[g["used_extra"] == 1, "extra_resin_weight_lbs"]
        rows.append({
            "Part Number":          _part_label(part),
            "Station":              station,
            "Total Dispenses":      total,
            "Used Extra":           int(used),
            "% Used Extra":         round(100 * used / total, 1),
            "Median Extra (lbs)":   round(extra_vals.median(), 2)
                                    if not extra_vals.empty else 0,
            "Max Extra (lbs)":      round(extra_vals.max(), 2)
                                    if not extra_vals.empty else 0,
        })
    return sorted(rows, key=lambda r: r["% Used Extra"], reverse=True)


# ── 5. Resin Use by Time ─────────────────────────────────────────────────────

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def build_resin_by_time(df: pd.DataFrame, resin_names: list,
                        breakdown: str = "hour",
                        part_filter: list = None) -> go.Figure:
    if df.empty:
        return _empty_fig("No data for the selected filters.")

    plot_df = df.copy()
    if part_filter:
        plot_df = plot_df[plot_df["first_part_number"].isin(part_filter)]
    if plot_df.empty:
        return _empty_fig("No data for the selected part numbers.")

    fig = go.Figure()

    if breakdown == "hour":
        x_col   = "hour"
        all_x   = list(range(24))
        x_labels = [f"{h:02d}:00" for h in all_x]
        x_title  = "Hour of Day"
    else:
        x_col   = "month"
        all_x   = list(range(1, 13))
        x_labels = MONTH_NAMES
        x_title  = "Month of Year"

    for station in resin_names:
        sub = plot_df[plot_df["resin_name"] == station].copy()
        if sub.empty:
            continue
        color = RESIN_COLORS.get(station, "#64748b")
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

        agg = (
            sub.groupby(x_col)["total_weight_lbs"]
            .agg(["mean", "std", "count"])
            .reindex(all_x)
            .reset_index()
        )
        agg["std"]   = agg["std"].fillna(0)
        agg["mean"]  = agg["mean"].fillna(np.nan)
        agg["upper"] = agg["mean"] + agg["std"]
        agg["lower"] = agg["mean"] - agg["std"]

        x_display = x_labels

        # Filled ±1 std dev band
        fig.add_trace(go.Scatter(
            x=x_display + x_display[::-1],
            y=list(agg["upper"]) + list(agg["lower"].iloc[::-1]),
            fill="toself",
            fillcolor=f"rgba({r},{g},{b},0.12)",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Mean line
        fig.add_trace(go.Scatter(
            x=x_display,
            y=agg["mean"],
            mode="lines+markers",
            name=station,
            line=dict(color=color, width=2),
            marker=dict(color=color, size=6),
            customdata=agg["count"].fillna(0).astype(int).values,
            hovertemplate=(
                "%{x}<br>"
                "Avg weight: %{y:.2f} lbs<br>"
                "N dispenses: %{customdata}<br>"
                "<extra></extra>"
            ),
        ))

    title = (
        "Average Resin Dispensed by Hour of Day"
        if breakdown == "hour"
        else "Average Resin Dispensed by Month of Year"
    )
    fig.update_layout(
        **_base_layout(title, x_title, "Avg Total Weight (lbs) ± 1σ"),
    )
    return fig


def _resin_by_time_stats(df: pd.DataFrame,
                         breakdown: str = "hour",
                         part_filter: list = None) -> list[dict]:
    if df.empty:
        return []
    plot_df = df.copy()
    if part_filter:
        plot_df = plot_df[plot_df["first_part_number"].isin(part_filter)]
    if plot_df.empty:
        return []
    x_col = breakdown
    rows = []
    for station in plot_df["resin_name"].unique():
        sub = plot_df[plot_df["resin_name"] == station]
        agg = sub.groupby(x_col)["total_weight_lbs"].agg(["mean", "count"])
        peak_x = agg["mean"].idxmax()
        low_x  = agg["mean"].idxmin()
        label_fn = (
            (lambda x: f"{x:02d}:00") if breakdown == "hour"
            else (lambda x: MONTH_NAMES[x - 1])
        )
        rows.append({
            "Station":              station,
            "Peak Period":          label_fn(peak_x),
            "Peak Avg (lbs)":       round(agg.loc[peak_x, "mean"], 2),
            "Lowest Period":        label_fn(low_x),
            "Lowest Avg (lbs)":     round(agg.loc[low_x, "mean"], 2),
            "Overall Mean (lbs)":   round(sub["total_weight_lbs"].mean(), 2),
            "Total Dispenses":      len(sub),
        })
    return rows


# ---------------------------------------------------------------------------
# Stats table column definitions per chart type
# ---------------------------------------------------------------------------

STATS_COLUMNS = {
    "part_count":   ["Station", "Part Number", "Count", "% of Station Total"],
    "resin_weight": ["Part Number", "Station", "N", "Nominal (lbs)",
                     "Median (lbs)", "Mean (lbs)", "Std Dev",
                     "Min (lbs)", "Max (lbs)"],
    "overshoot":    ["Station", "N", "Mean (lbs)", "Median (lbs)", "Std Dev",
                     "Min (lbs)", "Max (lbs)", "% Positive", "% Negative"],
    "extra_resin":  ["Part Number", "Station", "Total Dispenses", "Used Extra",
                     "% Used Extra", "Median Extra (lbs)", "Max Extra (lbs)"],
    "resin_by_time":["Station", "Peak Period", "Peak Avg (lbs)",
                     "Lowest Period", "Lowest Avg (lbs)",
                     "Overall Mean (lbs)", "Total Dispenses"],
}


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    date_start = (dt.date.today() - dt.timedelta(days=90)).isoformat()
    date_end   = dt.date.today().isoformat()

    return html.Div(
        style={"backgroundColor": "#f1f5f9", "minHeight": "100vh",
               "fontFamily": "Inter, sans-serif"},
        children=[

            navbar("Resin Analysis"),

            html.Div(style={"padding": "20px 28px"}, children=[
                dbc.Row([

                    # ── Sidebar ──────────────────────────────────────────────
                    dbc.Col(width=3, children=[

                        html.Div(style=PANEL, children=[
                            html.Label("Chart Type", style=LABEL),
                            dcc.Dropdown(
                                id="resin-chart-type",
                                options=CHART_TYPES,
                                value="part_count",
                                clearable=False,
                            ),
                        ]),

                        # Sort order — only shown for Part Count
                        html.Div(
                            id="resin-sort-wrapper",
                            style=PANEL,
                            children=[
                                html.Label("Sort By", style=LABEL),
                                dcc.RadioItems(
                                    id="resin-sort-by",
                                    options=[
                                        {"label": " Count (descending)", "value": "count"},
                                        {"label": " Part number",        "value": "part"},
                                    ],
                                    value="count",
                                    inputStyle={"marginRight": "6px"},
                                    labelStyle={"display": "block",
                                                "fontSize": "13px",
                                                "color": "#334155",
                                                "lineHeight": "2"},
                                ),
                            ],
                        ),

                        html.Div(style=PANEL, children=[
                            html.Label("Resin Station", style=LABEL),
                            dcc.Checklist(
                                id="resin-station-select",
                                options=[
                                    {"label": " Gray Resin", "value": "Gray Resin"},
                                    {"label": " Tan Resin",  "value": "Tan Resin"},
                                ],
                                value=["Gray Resin", "Tan Resin"],
                                inputStyle={"marginRight": "6px"},
                            ),
                        ]),

                        html.Div(style=PANEL, children=[
                            html.Label("Date Range", style=LABEL),
                            dcc.Dropdown(
                                id="resin-date-quick",
                                options=[
                                    {"label": "Last 90 days",  "value": "90d"},
                                    {"label": "This month",    "value": "this_month"},
                                    {"label": "Last month",    "value": "last_month"},
                                    {"label": "This week",     "value": "this_week"},
                                    {"label": "Last week",     "value": "last_week"},
                                    {"label": "This year",     "value": "this_year"},
                                    {"label": "All time",      "value": "all"},
                                ],
                                placeholder="Quick select...",
                                clearable=True,
                                style={"marginBottom": "8px"},
                            ),
                            html.Div("From", style={"fontSize": "12px",
                                     "color": "#64748b", "marginBottom": "4px"}),
                            dcc.DatePickerSingle(
                                id="resin-date-start",
                                date=date_start,
                                display_format="YYYY-MM-DD",
                                style={"width": "100%"},
                            ),
                            html.Div("To", style={"fontSize": "12px",
                                     "color": "#64748b",
                                     "marginBottom": "4px", "marginTop": "6px"}),
                            dcc.DatePickerSingle(
                                id="resin-date-end",
                                date=date_end,
                                display_format="YYYY-MM-DD",
                                style={"width": "100%"},
                            ),
                        ]),

                        # Secondary controls — shown/hidden by chart type
                        html.Div(
                            id="resin-aggr-wrapper",
                            style=PANEL,
                            children=[
                                html.Label("Aggregation", style=LABEL),
                                dcc.Dropdown(
                                    id="resin-aggr-select",
                                    options=AGGREGATION_LEVELS,
                                    value="D",
                                    clearable=False,
                                ),
                            ],
                        ),

                        html.Div(
                            id="resin-time-breakdown-wrapper",
                            style={**PANEL, "display": "none"},
                            children=[
                                html.Label("Time Breakdown", style=LABEL),
                                dcc.Dropdown(
                                    id="resin-time-breakdown",
                                    options=TIME_BREAKDOWN,
                                    value="hour",
                                    clearable=False,
                                ),
                            ],
                        ),

                        html.Div(
                            id="resin-part-filter-wrapper",
                            style={**PANEL, "display": "none"},
                            children=[
                                html.Label("Filter by Part Number", style=LABEL),
                                html.Div(style={
                                    "fontSize": "11px", "color": "#94a3b8",
                                    "marginBottom": "6px",
                                }, children="Leave blank to include all parts."),
                                dcc.Dropdown(
                                    id="resin-part-filter",
                                    options=[],
                                    multi=True,
                                    placeholder="Select part number(s)...",
                                ),
                            ],
                        ),

                        html.Button(
                            "Run",
                            id="resin-run-btn",
                            className="btn-primary",
                        ),

                        html.Div(id="resin-status", style={
                            "marginTop": "10px", "fontSize": "12px",
                            "color": "#64748b",
                            "fontFamily": "Inter, sans-serif",
                            "minHeight": "18px",
                        }),
                    ]),

                    # ── Main content ──────────────────────────────────────────
                    dbc.Col(width=9, children=[

                        html.Div(style=PANEL, children=[
                            dcc.Graph(
                                id="resin-chart",
                                figure=_empty_fig(),
                                config={"displayModeBar": True,
                                        "displaylogo": False},
                            ),
                        ]),

                        html.Div(style=PANEL, children=[
                            html.Div(style={
                                "display": "flex",
                                "justifyContent": "space-between",
                                "alignItems": "center",
                                "marginBottom": "10px",
                            }, children=[
                                html.Label("Summary Statistics",
                                           style={**LABEL, "marginBottom": "0",
                                                  "display": "inline-block"}),
                                html.Div(style={"display": "flex", "gap": "8px"},
                                         children=[
                                    html.Button(
                                        "Export Stats CSV",
                                        id="resin-export-stats-btn",
                                        style={
                                            "padding": "5px 12px",
                                            "backgroundColor": "#ffffff",
                                            "color": "#2563eb",
                                            "border": "1px solid #2563eb",
                                            "borderRadius": "5px",
                                            "fontFamily": "Inter, sans-serif",
                                            "fontSize": "12px",
                                            "fontWeight": "600",
                                            "cursor": "pointer",
                                        },
                                    ),
                                    html.Button(
                                        "Export Raw Data CSV",
                                        id="resin-export-raw-btn",
                                        style={
                                            "padding": "5px 12px",
                                            "backgroundColor": "#ffffff",
                                            "color": "#475569",
                                            "border": "1px solid #cbd5e1",
                                            "borderRadius": "5px",
                                            "fontFamily": "Inter, sans-serif",
                                            "fontSize": "12px",
                                            "fontWeight": "600",
                                            "cursor": "pointer",
                                        },
                                    ),
                                    dcc.Download(id="resin-stats-download"),
                                    dcc.Download(id="resin-raw-download"),
                                ]),
                            ]),
                            dash_table.DataTable(
                                id="resin-stats-table",
                                columns=[],
                                data=[],
                                style_table={"overflowX": "auto"},
                                style_header={
                                    "backgroundColor": "#f1f5f9",
                                    "color": "#475569", "fontWeight": "600",
                                    "fontSize": "12px",
                                    "border": "1px solid #e2e8f0",
                                    "padding": "10px 12px",
                                    "fontFamily": "Inter, sans-serif",
                                },
                                style_cell={
                                    "backgroundColor": "#ffffff",
                                    "color": "#1e293b", "fontSize": "13px",
                                    "border": "1px solid #e2e8f0",
                                    "padding": "8px 12px",
                                    "textAlign": "center",
                                    "fontFamily": "Inter, sans-serif",
                                },
                                style_data_conditional=[{
                                    "if": {"row_index": "odd"},
                                    "backgroundColor": "#f8fafc",
                                }],
                                sort_action="native",
                                page_size=20,
                            ),
                        ]),
                    ]),
                ]),
            ]),

            dcc.Store(id="resin-data-store"),
            dcc.Store(id="resin-stats-store"),
        ],
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def register_callbacks(app):

    # ── Quick-select date range ──
    @app.callback(
        Output("resin-date-start", "date"),
        Output("resin-date-end",   "date"),
        Input("resin-date-quick",  "value"),
        prevent_initial_call=True,
    )
    def resin_quick_select(value):
        today = dt.date.today()
        if value == "90d":
            return (today - dt.timedelta(days=90)).isoformat(), today.isoformat()
        elif value == "this_month":
            return today.replace(day=1).isoformat(), today.isoformat()
        elif value == "last_month":
            first_this = today.replace(day=1)
            last_prev  = first_this - dt.timedelta(days=1)
            return last_prev.replace(day=1).isoformat(), last_prev.isoformat()
        elif value == "this_week":
            monday = today - dt.timedelta(days=today.weekday())
            return monday.isoformat(), today.isoformat()
        elif value == "last_week":
            monday      = today - dt.timedelta(days=today.weekday())
            last_monday = monday - dt.timedelta(weeks=1)
            last_sunday = monday - dt.timedelta(days=1)
            return last_monday.isoformat(), last_sunday.isoformat()
        elif value == "this_year":
            return today.replace(month=1, day=1).isoformat(), today.isoformat()
        elif value == "all":
            return "2020-01-01", today.isoformat()
        return dash.no_update, dash.no_update

    # ── Show/hide secondary controls based on chart type ──
    @app.callback(
        Output("resin-aggr-wrapper",           "style"),
        Output("resin-time-breakdown-wrapper", "style"),
        Output("resin-sort-wrapper",           "style"),
        Output("resin-part-filter-wrapper",    "style"),
        Input("resin-chart-type",              "value"),
        prevent_initial_call=False,
    )
    def toggle_secondary_controls(chart_type):
        show = {**PANEL}
        hide = {**PANEL, "display": "none"}
        return (
            show if chart_type == "overshoot"     else hide,
            show if chart_type == "resin_by_time" else hide,
            show if chart_type == "part_count"    else hide,
            show if chart_type == "resin_by_time" else hide,
        )

    # ── Populate part number filter options from DB ──
    @app.callback(
        Output("resin-part-filter", "options"),
        Input("resin-chart-type",   "value"),
        prevent_initial_call=False,
    )
    def populate_part_options(chart_type):
        try:
            conn = get_connection(DB_PATH, read_only=True)
            df = pd.read_sql("""
                SELECT DISTINCT first_part_number
                FROM raw_resin_data
                WHERE first_part_number IS NOT NULL AND first_part_number != 0
                ORDER BY first_part_number
            """, conn)
            conn.close()
            parts = sorted(df["first_part_number"].dropna().astype(int).unique())
            return [{"label": _part_label(p), "value": p} for p in parts]
        except Exception:
            return []

    @app.callback(
        Output("resin-chart",       "figure"),
        Output("resin-stats-table", "data"),
        Output("resin-stats-table", "columns"),
        Output("resin-status",      "children"),
        Output("resin-data-store",  "data"),
        Output("resin-stats-store", "data"),
        Input("resin-run-btn",      "n_clicks"),
        State("resin-chart-type",     "value"),
        State("resin-station-select", "value"),
        State("resin-date-start",     "date"),
        State("resin-date-end",       "date"),
        State("resin-aggr-select",    "value"),
        State("resin-time-breakdown", "value"),
        State("resin-sort-by",        "value"),
        State("resin-part-filter",    "value"),
        prevent_initial_call=True,
    )
    def run_resin(n_clicks, chart_type, stations, date_start, date_end,
                  aggr, time_breakdown, sort_by, part_filter):
        if not stations:
            return (
                _empty_fig("Select at least one resin station."),
                [], [], "Select at least one resin station.", None, None,
            )

        try:
            df = load_resin_data(DB_PATH, stations, date_start, date_end)
        except Exception as e:
            return _empty_fig(f"Database error: {e}"), [], [], f"Error: {e}", None, None

        if df.empty:
            return (
                _empty_fig("No data found for the selected filters."),
                [], [], "No data found.", None, None,
            )

        # Build chart
        if chart_type == "part_count":
            fig   = build_part_count(df, stations, sort_by or "count")
            rows  = _part_count_stats(df)
        elif chart_type == "resin_weight":
            fig   = build_resin_weight(df, stations)
            rows  = _resin_weight_stats(df)
        elif chart_type == "overshoot":
            fig   = build_overshoot(df, stations, aggr or "D")
            rows  = _overshoot_stats(df)
        elif chart_type == "extra_resin":
            fig   = build_extra_resin(df, stations)
            rows  = _extra_resin_stats(df)
        elif chart_type == "resin_by_time":
            fig   = build_resin_by_time(df, stations, time_breakdown or "hour",
                                        part_filter or None)
            rows  = _resin_by_time_stats(df, time_breakdown or "hour",
                                         part_filter or None)
        else:
            fig, rows = _empty_fig(), []

        col_names = STATS_COLUMNS.get(chart_type, [])
        columns   = [{"name": c, "id": c} for c in col_names]
        status    = f"{len(df):,} dispense records loaded."

        # Serialize for export callbacks.
        # Drop the Timestamp column for JSON serialisation safety.
        df_export = df.copy()
        df_export["record_timestamp"] = df_export["record_timestamp"].astype(str)
        raw_json   = df_export.to_json(orient="split")
        stats_json = io.StringIO()
        pd.DataFrame(rows).to_json(stats_json, orient="split")
        stats_json = stats_json.getvalue()

        return fig, rows, columns, status, raw_json, stats_json

    # ── Export stats table as CSV ──
    @app.callback(
        Output("resin-stats-download",    "data"),
        Input("resin-export-stats-btn",   "n_clicks"),
        State("resin-stats-store",        "data"),
        State("resin-chart-type",         "value"),
        prevent_initial_call=True,
    )
    def export_stats_csv(n_clicks, stats_json, chart_type):
        if not stats_json:
            return None
        try:
            df_stats = pd.read_json(io.StringIO(stats_json), orient="split")
            if df_stats.empty:
                return None
            csv_str  = df_stats.to_csv(index=False)
            filename = (f"resin_{chart_type}_stats_"
                        f"{dt.datetime.now().strftime('%Y%m%d_%H%M')}.csv")
            return dcc.send_string(csv_str, filename)
        except Exception as e:
            print(f"Stats export error: {e}")
            return None

    # ── Export raw dispense data as CSV ──
    @app.callback(
        Output("resin-raw-download",    "data"),
        Input("resin-export-raw-btn",   "n_clicks"),
        State("resin-data-store",       "data"),
        prevent_initial_call=True,
    )
    def export_raw_csv(n_clicks, raw_json):
        if not raw_json:
            return None
        try:
            df_raw = pd.read_json(io.StringIO(raw_json), orient="split")
            if df_raw.empty:
                return None
            # Drop internal derived columns that aren't meaningful outside
            # the app (hour, month, month_name, used_extra are easily
            # re-derived; keeping the raw source columns is most useful)
            drop_cols = [c for c in ["hour", "month", "month_name", "used_extra"]
                         if c in df_raw.columns]
            df_raw = df_raw.drop(columns=drop_cols)
            csv_str  = df_raw.to_csv(index=False)
            filename = (f"resin_raw_data_"
                        f"{dt.datetime.now().strftime('%Y%m%d_%H%M')}.csv")
            return dcc.send_string(csv_str, filename)
        except Exception as e:
            print(f"Raw export error: {e}")
            return None
