"""
cycle_analysis_page.py

Cycle Analysis page for the Dash app.

Allows free-form scatter plot exploration of cycle and stage time data.
Each point is one cycle. Axes, color coding, and filters are all
user-selectable.

Import in app.py and call register_callbacks(app).
"""

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc

from analytics import get_connection, get_cycles_for_explorer, get_operators_by_shift

DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"
MOLDS   = ["Brown", "Purple", "Red", "Pink", "Orange", "Green"]

# ---------------------------------------------------------------------------
# Axis options
# ---------------------------------------------------------------------------

Y_AXIS_OPTIONS = [
    {"label": "Cycle Time (min)",  "value": "cycle_time"},
    {"label": "Layup Time (min)",  "value": "layup_time"},
    {"label": "Close Time (min)",  "value": "close_time"},
    {"label": "Resin Time (min)",  "value": "resin_time"},
]

X_AXIS_OPTIONS = [
    {"label": "Date / Time",          "value": "cycle_timestamp"},
    {"label": "Time of Day (hour)",   "value": "hour_of_day"},
    {"label": "Day of Week",          "value": "day_name"},
    {"label": "Cycle Time (min)",     "value": "cycle_time"},
    {"label": "Layup Time (min)",     "value": "layup_time"},
    {"label": "Close Time (min)",     "value": "close_time"},
    {"label": "Resin Time (min)",     "value": "resin_time"},
    {"label": "Bag Cycle Count",      "value": "bag_cycles"},
    {"label": "Bag Days in Service",  "value": "bag_days"},
]

COLOR_OPTIONS = [
    {"label": "None",        "value": "none"},
    {"label": "Mold",        "value": "mold_name"},
    {"label": "Operator",    "value": "operator_name"},
    {"label": "Shift",       "value": "shift"},
    {"label": "Day of Week", "value": "day_name"},
]

# Ordered categories for day-of-week axis/color
DAY_ORDER = ["Monday", "Tuesday", "Wednesday",
             "Thursday", "Friday", "Saturday", "Sunday"]

# Color palette for categorical traces
PALETTE = [
    "#2563eb", "#dc2626", "#16a34a", "#d97706",
    "#7c3aed", "#0891b2", "#be185d", "#65a30d",
    "#f59e0b", "#6366f1", "#14b8a6", "#f43f5e",
]

# Mold colors match the physical mold color names
MOLD_COLORS = {
    "Brown":  "#92400e",
    "Purple": "#7c3aed",
    "Red":    "#dc2626",
    "Pink":   "#db2777",
    "Orange": "#ea580c",
    "Green":  "#16a34a",
}

# ---------------------------------------------------------------------------
# Shared styles
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
# Plot builder
# ---------------------------------------------------------------------------

def build_scatter(df: pd.DataFrame, x_col: str, y_col: str,
                  color_col: str) -> go.Figure:
    """
    Build an interactive Plotly scatter plot from the explorer DataFrame.

    Points have lowered opacity (0.35) so dense regions show their
    density naturally through overlapping colour rather than a solid block.
    When coloring by mold, uses the actual mold colors.
    When x-axis is cycle_timestamp, Plotly renders a proper time axis.
    """
    fig = go.Figure()

    if df is None or df.empty:
        fig.update_layout(
            title=dict(text="Set filters and click Run",
                       font=dict(size=14, color="#64748b")),
            paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc", height=520,
        )
        return fig

    # Drop rows missing either axis value
    plot_df = df.dropna(subset=[x_col, y_col]).copy()

    if plot_df.empty:
        fig.update_layout(
            title=dict(text="No data for the selected axes and filters.",
                       font=dict(size=14, color="#64748b")),
            paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc", height=520,
        )
        return fig

    x_label = next((o["label"] for o in X_AXIS_OPTIONS if o["value"] == x_col),
                   x_col)
    y_label = next((o["label"] for o in Y_AXIS_OPTIONS if o["value"] == y_col),
                   y_col)

    def make_trace(subset, name, color):
        return go.Scatter(
            x=subset[x_col],
            y=subset[y_col],
            mode="markers",
            name=name,
            marker=dict(color=color, size=5, opacity=0.35),
            hovertemplate=(
                f"{x_label}: %{{x}}<br>"
                f"{y_label}: %{{y:.2f}} min<br>"
                "Mold: %{customdata[0]}<br>"
                "Operator: %{customdata[1]}<br>"
                "Shift: %{customdata[2]}<br>"
                "%{customdata[3]}"
                "<extra></extra>"
            ),
            customdata=subset[["mold_name", "operator_name",
                                "shift", "cycle_timestamp"]].values,
        )

    if color_col == "none" or color_col not in plot_df.columns:
        fig.add_trace(make_trace(plot_df, "All cycles", "#2563eb"))

    elif color_col == "mold_name":
        # Use actual mold colors
        for mold_name in sorted(plot_df["mold_name"].dropna().unique()):
            color  = MOLD_COLORS.get(mold_name, "#64748b")
            subset = plot_df[plot_df["mold_name"] == mold_name]
            fig.add_trace(make_trace(subset, mold_name, color))

    else:
        # Generic categorical coloring
        if color_col == "day_name":
            categories = [d for d in DAY_ORDER
                          if d in plot_df[color_col].unique()]
        else:
            categories = sorted(plot_df[color_col].dropna().unique())

        for j, cat in enumerate(categories):
            color  = PALETTE[j % len(PALETTE)]
            subset = plot_df[plot_df[color_col] == cat]
            fig.add_trace(make_trace(subset, str(cat), color))

    # Axis type overrides
    xaxis_kwargs = dict(
        title=x_label, gridcolor="#e2e8f0",
        color="#475569", zeroline=False,
    )
    if x_col == "cycle_timestamp":
        xaxis_kwargs["type"] = "date"
    elif x_col == "day_name":
        xaxis_kwargs["categoryorder"] = "array"
        xaxis_kwargs["categoryarray"] = DAY_ORDER

    fig.update_layout(
        title=dict(
            text=f"{y_label} vs {x_label}",
            font=dict(size=15, color="#1e293b"),
            x=0,
        ),
        xaxis=xaxis_kwargs,
        yaxis=dict(title=y_label, gridcolor="#e2e8f0",
                   color="#475569", zeroline=False),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#1e293b", family="Inter, sans-serif"),
        legend=dict(bgcolor="#ffffff", bordercolor="#e2e8f0",
                    borderwidth=1, font=dict(size=12)),
        margin=dict(l=60, r=20, t=60, b=40),
        height=520,
        hovermode="closest",
    )
    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    conn       = get_connection(DB_PATH)
    by_shift   = get_operators_by_shift(conn)
    conn.close()

    # Build operator options grouped by shift
    op_options = []
    for shift in ["Day", "Swing", "Graveyard"]:
        ops = by_shift.get(shift, [])
        for op in ops:
            op_options.append({
                "label": f"{op['name']} ({op['employee_number']}) — {shift}",
                "value": op["employee_number"],
            })

    date_start = (dt.date.today() - dt.timedelta(days=90)).isoformat()
    date_end   = dt.date.today().isoformat()

    return html.Div(
        style={"backgroundColor": "#f1f5f9", "minHeight": "100vh",
               "fontFamily": "Inter, sans-serif"},
        children=[

            # Header
            html.Div(style={
                "backgroundColor": "#1e293b", "padding": "14px 28px",
                "display": "flex", "alignItems": "center",
                "justifyContent": "space-between",
            }, children=[
                html.Div([
                    html.Span("ROCKWELL MANUFACTURING", style={
                        "fontSize": "11px", "fontWeight": "600",
                        "color": "#94a3b8", "letterSpacing": "0.15em",
                        "fontFamily": "Inter, sans-serif",
                    }),
                    html.H1("Cycle Analysis", style={
                        "margin": "2px 0 0 0", "fontSize": "20px",
                        "fontWeight": "500", "color": "#f8fafc",
                        "fontFamily": "Inter, sans-serif",
                    }),
                ]),
                html.Div(style={"display": "flex", "gap": "20px"}, children=[
                    dcc.Link("← Operator Performance", href="/",
                             style={"color": "#94a3b8", "fontSize": "13px",
                                    "fontFamily": "Inter, sans-serif",
                                    "textDecoration": "none"}),
                    dcc.Link("Operator Management →", href="/operators",
                             style={"color": "#94a3b8", "fontSize": "13px",
                                    "fontFamily": "Inter, sans-serif",
                                    "textDecoration": "none"}),
                ]),
            ]),

            html.Div(style={"padding": "20px 28px"}, children=[
                dbc.Row([

                    # Sidebar
                    dbc.Col(width=3, children=[

                        # Axes
                        html.Div(className="panel", children=[
                            html.Label("Y Axis", style=LABEL),
                            dcc.Dropdown(
                                id="explorer-y",
                                options=Y_AXIS_OPTIONS,
                                value="cycle_time",
                                clearable=False,
                            ),
                            html.Label("X Axis", style={**LABEL,
                                       "marginTop": "12px"}),
                            dcc.Dropdown(
                                id="explorer-x",
                                options=X_AXIS_OPTIONS,
                                value="hour_of_day",
                                clearable=False,
                            ),
                            html.Label("Color By", style={**LABEL,
                                       "marginTop": "12px"}),
                            dcc.Dropdown(
                                id="explorer-color",
                                options=COLOR_OPTIONS,
                                value="none",
                                clearable=False,
                            ),
                        ]),

                        # Filters
                        html.Div(className="panel", children=[
                            html.Label("Mold", style=LABEL),
                            dcc.Dropdown(
                                id="explorer-mold",
                                options=[{"label": "All Molds", "value": ""}]
                                        + [{"label": m, "value": m}
                                           for m in MOLDS],
                                value="",
                                clearable=False,
                            ),

                            html.Label("Operators", style={**LABEL,
                                       "marginTop": "12px"}),
                            html.Div(style={"fontSize": "11px",
                                           "color": "#94a3b8",
                                           "marginBottom": "6px"}, children=[
                                "Leave blank to include all operators."
                            ]),
                            dcc.Dropdown(
                                id="explorer-operators",
                                options=op_options,
                                multi=True,
                                placeholder="Filter by operator(s)...",
                            ),

                            html.Label("Date Range", style={**LABEL,
                                       "marginTop": "12px"}),
                            html.Div("From", style={"fontSize": "12px",
                                     "color": "#64748b",
                                     "marginBottom": "4px"}),
                            dcc.Input(
                                id="explorer-date-start",
                                type="text",
                                value=date_start,
                                placeholder="YYYY-MM-DD",
                                debounce=True,
                                style=INPUT_STYLE,
                            ),
                            html.Div("To", style={"fontSize": "12px",
                                     "color": "#64748b",
                                     "marginBottom": "4px",
                                     "marginTop": "6px"}),
                            dcc.Input(
                                id="explorer-date-end",
                                type="text",
                                value=date_end,
                                placeholder="YYYY-MM-DD",
                                debounce=True,
                                style=INPUT_STYLE,
                            ),

                            html.Label("Options", style={**LABEL,
                                       "marginTop": "12px"}),
                            dcc.Checklist(
                                id="explorer-options",
                                options=[{
                                    "label": " Include flagged cycles",
                                    "value": "include_flagged",
                                }],
                                value=[],
                                inputStyle={"marginRight": "6px"},
                                labelStyle={
                                    "fontSize": "13px", "color": "#334155",
                                    "lineHeight": "2", "cursor": "pointer",
                                },
                            ),
                        ]),

                        html.Button("Run", id="explorer-run-btn", style={
                            "width": "100%", "padding": "10px",
                            "backgroundColor": "#2563eb", "color": "#ffffff",
                            "border": "none", "borderRadius": "6px",
                            "fontFamily": "Inter, sans-serif",
                            "fontWeight": "600", "fontSize": "14px",
                            "cursor": "pointer", "marginBottom": "8px",
                        }),

                        html.Div(id="explorer-status", style={
                            "fontSize": "12px", "color": "#64748b",
                            "minHeight": "18px",
                        }),
                    ]),

                    # Main content
                    dbc.Col(width=9, children=[

                        html.Div(className="panel", children=[
                            dcc.Graph(
                                id="explorer-scatter",
                                figure=build_scatter(None, "hour_of_day",
                                                     "cycle_time", "none"),
                                config={"displayModeBar": True,
                                        "displaylogo": False},
                            ),
                        ]),

                        html.Div(className="panel", children=[
                            html.Label("Summary Statistics", style=LABEL),
                            dash_table.DataTable(
                                id="explorer-stats-table",
                                columns=[{"name": c, "id": c} for c in
                                         ["Group", "N", "Median", "Mean",
                                          "Std Dev", "Min", "Max"]],
                                data=[],
                                style_table={"overflowX": "auto"},
                                style_header={
                                    "backgroundColor": "#f1f5f9",
                                    "color": "#475569", "fontWeight": "600",
                                    "fontSize": "12px",
                                    "border": "1px solid #e2e8f0",
                                    "padding": "10px 12px",
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
                                page_size=15,
                            ),
                        ]),
                    ]),
                ]),
            ]),
        ]
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def register_callbacks(app):

    @app.callback(
        Output("explorer-scatter",     "figure"),
        Output("explorer-stats-table", "data"),
        Output("explorer-status",      "children"),
        Input("explorer-run-btn",      "n_clicks"),
        State("explorer-y",            "value"),
        State("explorer-x",            "value"),
        State("explorer-color",        "value"),
        State("explorer-mold",         "value"),
        State("explorer-operators",    "value"),
        State("explorer-date-start",   "value"),
        State("explorer-date-end",     "value"),
        State("explorer-options",      "value"),
        prevent_initial_call=True,
    )
    def run_explorer(n_clicks, y_col, x_col, color_col, mold,
                     emp_numbers, date_start, date_end, options):

        exclude_flagged = "include_flagged" not in (options or [])

        try:
            conn = get_connection(DB_PATH)
            df   = get_cycles_for_explorer(
                conn,
                mold_name        = mold or None,
                date_start       = date_start,
                date_end         = date_end,
                employee_numbers = emp_numbers or None,
                exclude_flagged  = exclude_flagged,
            )
            conn.close()
        except Exception as e:
            empty_fig = build_scatter(None, x_col, y_col, color_col)
            return empty_fig, [], f"Database error: {e}"

        if df.empty:
            empty_fig = build_scatter(None, x_col, y_col, color_col)
            return empty_fig, [], "No data found for the selected filters."

        fig    = build_scatter(df, x_col, y_col, color_col)
        status = f"{len(df):,} cycles loaded."

        # Build summary stats table grouped by the color column
        stats_rows = _build_stats_table(df, y_col, color_col)

        return fig, stats_rows, status


def _build_stats_table(df: pd.DataFrame, y_col: str,
                       color_col: str) -> list[dict]:
    """
    Build summary stats for the explorer, grouped by the color column
    (or a single 'All' row if color is none).
    """
    y_label = next((o["label"] for o in Y_AXIS_OPTIONS if o["value"] == y_col),
                   y_col)

    def stats_for(subset, label):
        vals = subset[y_col].dropna()
        if len(vals) == 0:
            return None
        return {
            "Group":   label,
            "N":       len(vals),
            "Median":  round(vals.median(), 2),
            "Mean":    round(vals.mean(), 2),
            "Std Dev": round(vals.std(), 2),
            "Min":     round(vals.min(), 2),
            "Max":     round(vals.max(), 2),
        }

    rows = []
    if color_col == "none" or color_col not in df.columns:
        row = stats_for(df, "All cycles")
        if row:
            rows.append(row)
    else:
        if color_col == "day_name":
            categories = [d for d in DAY_ORDER
                          if d in df[color_col].unique()]
        else:
            categories = sorted(df[color_col].dropna().unique())

        for cat in categories:
            row = stats_for(df[df[color_col] == cat], str(cat))
            if row:
                rows.append(row)

    return rows
