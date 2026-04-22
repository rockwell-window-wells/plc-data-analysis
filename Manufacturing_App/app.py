"""
app.py

Dash 4 cycle time reporting app.

Key decisions vs previous version:
- Date pickers replaced with plain html.Input(type="date") -- Dash 4's
  dcc.DatePickerSingle ignores the date= prop and has unpredictable styling.
  Native HTML date inputs always show the default value and use the browser's
  built-in picker, which is readable and reliable.
- All CSS is injected via app.index_string <style> tag, which is guaranteed
  to load before any component renders. No assets/ folder needed.

Run:
    python app.py

Dependencies:
    pip install dash dash-bootstrap-components plotly pandas fpdf2 matplotlib seaborn
"""

import datetime as dt
import tempfile
import os

import pandas as pd
import plotly.graph_objects as go

import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc

import yaml

from analytics import (
    get_connection, get_operator_cycle_times,
    get_shift_cycle_times, get_all_cycles, get_operators_by_shift,
)
import operators_page
import cycle_analysis_page

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CONFIG_FILE = 'config_vars.yaml'

with open(CONFIG_FILE, 'r') as file:
    config_data = yaml.safe_load(file)
    DB_PATH = config_data['db_path']
# DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"
MOLDS   = ["Brown", "Purple", "Red", "Pink", "Orange", "Green"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_active_operators():
    try:
        conn = get_connection(DB_PATH)
        df = pd.read_sql("""
            SELECT employee_number, name
            FROM operators
            WHERE active_to IS NULL
            ORDER BY name ASC
        """, conn)
        conn.close()
        return [
            {
                "label": f"{row['name']} ({int(row['employee_number'])})",
                "value": int(row["employee_number"]),
            }
            for _, row in df.iterrows()
        ]
    except Exception as e:
        print(f"Error loading operators: {e}")
        return []


def build_plotly_boxplot(frames, baseline_count=0):
    """Build an interactive Plotly boxplot. One trace per operator/group.

    frames[0:baseline_count] are baseline traces (shift or all-shifts),
    rendered in grey with dashed lines. The rest are individual operators
    in colour.
    """
    fig = go.Figure()

    if not frames:
        fig.update_layout(
            title=dict(
                text="Select operators and click Run Report",
                font=dict(size=14, color="#64748b"),
            ),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#f8fafc",
            height=420,
        )
        return fig

    # Sort only the non-baseline frames by median; baselines stay first
    baselines   = [df for df in frames[:baseline_count] if not df.empty]
    individuals = sorted(
        [df for df in frames[baseline_count:] if not df.empty],
        key=lambda df: df["cycle_time"].median(),
    )
    ordered = baselines + individuals

    palette = ["#2563eb", "#dc2626", "#16a34a", "#d97706",
               "#7c3aed", "#0891b2", "#be185d", "#65a30d"]

    for i, df in enumerate(ordered):
        is_baseline = i < len(baselines)
        if is_baseline:
            color     = "#94a3b8"
            fillcolor = "rgba(148,163,184,0.15)"
            opacity   = 1.0
        else:
            color     = palette[(i - len(baselines)) % len(palette)]
            # Convert hex to rgba with low alpha for the fill
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            fillcolor = f"rgba({r},{g},{b},0.15)"
            opacity   = 1.0

        fig.add_trace(go.Box(
            y=df["cycle_time"],
            name=df["name"].iloc[0],
            boxpoints="outliers",
            marker=dict(color=color, size=5, opacity=0.6),
            line=dict(color=color, width=2),
            fillcolor=fillcolor,
            opacity=opacity,
        ))

    fig.update_layout(
        title=dict(
            text="Cycle Time Distribution by Operator",
            font=dict(size=15, color="#1e293b"),
            x=0,
        ),
        yaxis=dict(
            title="Cycle Time (min)",
            gridcolor="#e2e8f0",
            color="#475569",
            zeroline=False,
        ),
        xaxis=dict(color="#475569"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#1e293b", family="Inter, sans-serif"),
        legend=dict(bgcolor="#ffffff", bordercolor="#e2e8f0", borderwidth=1),
        margin=dict(l=60, r=20, t=60, b=40),
        height=420,
    )
    return fig


def build_stats_rows(frames):
    rows = []
    for df in frames:
        if df.empty:
            continue
        ct = df["cycle_time"].dropna()
        if len(ct) == 0:
            continue
        rows.append({
            "Operator": df["name"].iloc[0],
            "Emp #":    int(df["employee_number"].iloc[0]),
            "Cycles":   len(ct),
            "Median":   round(ct.median(), 1),
            "Mean":     round(ct.mean(), 1),
            "Std Dev":  round(ct.std(), 1),
            "Min":      round(ct.min(), 1),
            "Max":      round(ct.max(), 1),
        })
    return sorted(rows, key=lambda r: r["Median"])


def generate_pdf_bytes(frames, date_start, date_end, mold_filter):
    from fpdf import FPDF, XPos, YPos
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    if frames:
        combined = pd.concat(frames, ignore_index=True).dropna(subset=["cycle_time"])
        order = (combined.groupby("name")["cycle_time"]
                 .median().sort_values().index.tolist())
    else:
        combined = pd.DataFrame()
        order = []

    fig, ax = plt.subplots(figsize=(10, 4.5))
    if not combined.empty:
        sns.set_theme(style="whitegrid")
        sns.boxplot(
            data=combined, x="name", y="cycle_time", order=order,
            color="#2563eb", ax=ax,
            flierprops=dict(marker="o", markerfacecolor="none",
                            markersize=4, linestyle="none"),
        )
        for i, name in enumerate(order):
            vals = combined[combined["name"] == name]["cycle_time"].dropna()
            ax.text(i, ax.get_ylim()[0],
                    f"n={len(vals)}\nmed={vals.median():.1f}",
                    ha="center", va="bottom", fontsize=8, color="#64748b")
    ax.set_xlabel("Operator")
    ax.set_ylabel("Cycle Time (min)")
    ax.set_title("Cycle Time by Operator")
    plt.xticks(rotation=25, ha="right")
    fig.tight_layout()

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, dpi=150, bbox_inches="tight")
    tmp.close()
    plt.close(fig)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "Cycle Time Report",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6,
             f"Date range: {date_start or 'All time'} to {date_end or 'present'}"
             f"   |   Mold: {mold_filter or 'All molds'}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6,
             f"Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.image(tmp.name, x=10, w=190)
    os.unlink(tmp.name)
    pdf.ln(4)

    rows = build_stats_rows(frames)
    if rows:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, "Summary Statistics",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        cols   = ["Operator", "Cycles", "Median", "Mean", "Std Dev", "Min", "Max"]
        widths = [52, 20, 26, 26, 26, 20, 20]
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(226, 232, 240)
        for col, w in zip(cols, widths):
            pdf.cell(w, 7, col, border=1, fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for i, row in enumerate(rows):
            pdf.set_fill_color(248, 250, 252) if i % 2 == 0 \
                else pdf.set_fill_color(255, 255, 255)
            for val, w in zip(
                [row["Operator"], str(row["Cycles"]), str(row["Median"]),
                 str(row["Mean"]), str(row["Std Dev"]),
                 str(row["Min"]), str(row["Max"])],
                widths
            ):
                pdf.cell(w, 6, val, border=1, fill=True)
            pdf.ln()

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Cycle Time Reports",
    suppress_callback_exceptions=True,
)
server = app.server

# Default dates
DATE_START = (dt.date.today() - dt.timedelta(days=90)).isoformat()
DATE_END   = dt.date.today().isoformat()

# All CSS is in index_string so it loads before any component and cannot
# be overridden by Bootstrap or Dash component stylesheets.
app.index_string = """<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Inter, sans-serif;
            background-color: #f1f5f9;
            color: #1e293b;
        }

        /* ── Panels ── */
        .panel {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }

        .section-label {
            display: block;
            font-size: 11px;
            font-weight: 600;
            color: #475569;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        /* ── Native date inputs ── */
        input[type="date"] {
            width: 100%;
            padding: 7px 10px;
            font-family: Inter, sans-serif;
            font-size: 13px;
            color: #1e293b;
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            outline: none;
            cursor: pointer;
        }
        input[type="date"]:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
        }

        /* ── Dropdown (Dash 4 confirmed class names) ── */
        .dash-dropdown {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }
        .dash-dropdown-grid-container {
            background-color: #ffffff !important;
            min-height: 36px !important;
            padding: 4px 8px !important;
            align-items: center !important;
        }
        .dash-dropdown-placeholder {
            color: #94a3b8 !important;
            font-size: 13px !important;
        }
        .dash-dropdown-value {
            color: #1e293b !important;
            font-size: 13px !important;
        }
        .dash-dropdown-trigger-icon {
            color: #64748b !important;
        }
        /* Option list */
        .dash-options-list-option {
            background-color: #ffffff !important;
            color: #1e293b !important;
            font-size: 13px !important;
        }
        .dash-options-list-option:hover {
            background-color: #eff6ff !important;
        }
        .dash-options-list-option[aria-selected="true"] {
            background-color: #dbeafe !important;
            color: #1e40af !important;
        }
        .dash-options-list-option-text {
            color: inherit !important;
        }
        /* Multi-select tags */
        .dash-dropdown-tag {
            background-color: #dbeafe !important;
            border: 1px solid #93c5fd !important;
            border-radius: 4px !important;
            color: #1e40af !important;
            font-size: 12px !important;
        }
        .dash-dropdown-tag-value { color: #1e40af !important; }
        .dash-dropdown-tag-remove { color: #1e40af !important; }
        .dash-dropdown-tag-remove:hover {
            background-color: #bfdbfe !important;
        }

        /* ── Buttons ── */
        .btn-primary {
            width: 100%;
            padding: 10px;
            background-color: #2563eb;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-family: Inter, sans-serif;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            margin-bottom: 8px;
        }
        .btn-primary:hover { background-color: #1d4ed8; }

        .btn-secondary {
            width: 100%;
            padding: 10px;
            background-color: #ffffff;
            color: #2563eb;
            border: 1px solid #2563eb;
            border-radius: 6px;
            font-family: Inter, sans-serif;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
        }
        .btn-secondary:hover { background-color: #eff6ff; }

        /* ── Checklist ── */
        .dash-checklist label {
            color: #334155 !important;
            font-size: 13px !important;
            line-height: 2.2 !important;
            cursor: pointer !important;
        }

        /* ── Input helper labels ── */
        .input-sublabel {
            font-size: 12px;
            color: #64748b;
            margin-bottom: 4px;
            margin-top: 6px;
        }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>"""


def reports_layout():
    return html.Div(
    style={"backgroundColor": "#f1f5f9", "minHeight": "100vh"},
    children=[

        # Header
        html.Div(style={
            "backgroundColor": "#1e293b",
            "padding": "14px 28px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
        }, children=[
            html.Div([
                html.Span("ROCKWELL MANUFACTURING", style={
                    "fontSize": "11px", "fontWeight": "600",
                    "color": "#94a3b8", "letterSpacing": "0.15em",
                    "fontFamily": "Inter, sans-serif",
                }),
                html.H1("Operator Performance", style={
                    "margin": "2px 0 0 0", "fontSize": "20px",
                    "fontWeight": "500", "color": "#f8fafc",
                    "fontFamily": "Inter, sans-serif",
                }),
            ]),
            html.Div(style={"display": "flex", "alignItems": "center", "gap": "20px"}, children=[
                html.Div(id="last-updated", style={
                    "fontSize": "12px", "color": "#94a3b8",
                    "fontFamily": "Inter, sans-serif",
                }),
                dcc.Link("Cycle Analysis →", href="/cycle-analysis",
                         style={"color": "#94a3b8", "fontSize": "13px",
                                "fontFamily": "Inter, sans-serif",
                                "textDecoration": "none"}),
                dcc.Link("Operator Management →", href="/operators",
                         style={"color": "#94a3b8", "fontSize": "13px",
                                "fontFamily": "Inter, sans-serif",
                                "textDecoration": "none"}),
            ]),
        ]),

        # Body
        html.Div(style={"padding": "20px 28px"}, children=[
            dbc.Row([

                # Sidebar
                dbc.Col(width=3, children=[

                    html.Div(className="panel", children=[
                        html.Label("Select by Shift", className="section-label"),
                        dcc.Dropdown(
                            id="shift-dropdown",
                            options=[
                                {"label": "Day",       "value": "Day"},
                                {"label": "Swing",     "value": "Swing"},
                                {"label": "Graveyard", "value": "Graveyard"},
                            ],
                            placeholder="Quick-select a shift...",
                            clearable=True,
                        ),
                        html.Label("Operators", className="section-label",
                                   style={"marginTop": "10px"}),
                        dcc.Dropdown(
                            id="operator-dropdown",
                            options=load_active_operators(),
                            multi=True,
                            placeholder="Select operators...",
                        ),
                    ]),

                    html.Div(className="panel", children=[
                        html.Label("Compare Against", className="section-label"),
                        dcc.Dropdown(
                            id="comparison-dropdown",
                            options=[
                                {"label": "None",            "value": "none"},
                                {"label": "Shift baseline",  "value": "shift"},
                                {"label": "All shifts",      "value": "all"},
                            ],
                            value="none",
                            clearable=False,
                        ),
                        html.Div(
                            id="comparison-shift-wrapper",
                            style={"display": "none", "marginTop": "8px"},
                            children=[
                                html.Label("Shift to compare against",
                                           className="section-label"),
                                dcc.Dropdown(
                                    id="comparison-shift-dropdown",
                                    options=[
                                        {"label": "Day",       "value": "Day"},
                                        {"label": "Swing",     "value": "Swing"},
                                        {"label": "Graveyard", "value": "Graveyard"},
                                    ],
                                    placeholder="Select shift...",
                                    clearable=False,
                                ),
                            ],
                        ),
                    ]),

                    html.Div(className="panel", children=[
                        html.Label("Mold", className="section-label"),
                        dcc.Dropdown(
                            id="mold-dropdown",
                            options=[{"label": "All Molds", "value": ""}]
                                    + [{"label": m, "value": m} for m in MOLDS],
                            value="",
                            clearable=False,
                        ),
                    ]),

                    html.Div(className="panel", children=[
                        html.Label("Date Range", className="section-label"),
                        html.Div("From", className="input-sublabel"),
                        dcc.Input(
                            id="date-start",
                            type="text",
                            value=DATE_START,
                            placeholder="YYYY-MM-DD",
                            debounce=True,
                            style={
                                "width": "100%",
                                "padding": "7px 10px",
                                "fontFamily": "Inter, sans-serif",
                                "fontSize": "13px",
                                "color": "#1e293b",
                                "backgroundColor": "#ffffff",
                                "border": "1px solid #cbd5e1",
                                "borderRadius": "6px",
                                "outline": "none",
                            },
                        ),
                        html.Div("To", className="input-sublabel"),
                        dcc.Input(
                            id="date-end",
                            type="text",
                            value=DATE_END,
                            placeholder="YYYY-MM-DD",
                            debounce=True,
                            style={
                                "width": "100%",
                                "padding": "7px 10px",
                                "fontFamily": "Inter, sans-serif",
                                "fontSize": "13px",
                                "color": "#1e293b",
                                "backgroundColor": "#ffffff",
                                "border": "1px solid #cbd5e1",
                                "borderRadius": "6px",
                                "outline": "none",
                            },
                        ),
                    ]),

                    html.Div(className="panel", children=[
                        html.Label("Options", className="section-label"),
                        dcc.Checklist(
                            id="options-checklist",
                            options=[
                                {"label": " Full cycle only",
                                 "value": "full_cycle_only"},
                                {"label": " Exclude flagged cycles",
                                 "value": "exclude_flagged"},
                            ],
                            value=["full_cycle_only", "exclude_flagged"],
                            inputStyle={"marginRight": "6px"},
                        ),
                    ]),

                    html.Button(
                        "Run Report",
                        id="run-btn",
                        className="btn-primary",
                    ),
                    html.Button(
                        "Export PDF",
                        id="pdf-btn",
                        className="btn-secondary",
                    ),
                    dcc.Download(id="pdf-download"),

                    html.Div(id="status-msg", style={
                        "marginTop": "10px",
                        "fontSize": "12px",
                        "color": "#64748b",
                        "fontFamily": "Inter, sans-serif",
                        "minHeight": "18px",
                    }),
                ]),

                # Main content
                dbc.Col(width=9, children=[

                    html.Div(className="panel", children=[
                        dcc.Graph(
                            id="boxplot",
                            figure=build_plotly_boxplot([]),
                            config={"displayModeBar": True, "displaylogo": False},
                        ),
                    ]),

                    html.Div(className="panel", children=[
                        html.Label("Summary Statistics", className="section-label"),
                        dash_table.DataTable(
                            id="stats-table",
                            columns=[{"name": c, "id": c} for c in
                                     ["Operator", "Emp #", "Cycles", "Median",
                                      "Mean", "Std Dev", "Min", "Max"]],
                            data=[],
                            style_table={"overflowX": "auto"},
                            style_header={
                                "backgroundColor": "#f1f5f9",
                                "color": "#475569",
                                "fontWeight": "600",
                                "fontSize": "12px",
                                "border": "1px solid #e2e8f0",
                                "padding": "10px 12px",
                                "fontFamily": "Inter, sans-serif",
                            },
                            style_cell={
                                "backgroundColor": "#ffffff",
                                "color": "#1e293b",
                                "fontSize": "13px",
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

            dcc.Store(id="report-store"),
        ]),
    ],
)


# ---------------------------------------------------------------------------
# Top-level routing layout
# ---------------------------------------------------------------------------

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content"),
])


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def display_page(pathname):
    if pathname == "/operators":
        return operators_page.layout()
    if pathname == "/cycle-analysis":
        return cycle_analysis_page.layout()
    return reports_layout()


# Register page callbacks
operators_page.register_callbacks(app)
cycle_analysis_page.register_callbacks(app)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@app.callback(
    Output("operator-dropdown", "value"),
    Input("shift-dropdown",     "value"),
    prevent_initial_call=True,
)
def select_shift_operators(shift):
    """Populate the operator dropdown with all operators on the chosen shift."""
    if not shift:
        return []
    conn = get_connection(DB_PATH)
    by_shift = get_operators_by_shift(conn)
    conn.close()
    ops = by_shift.get(shift, [])
    return [op["employee_number"] for op in ops]


@app.callback(
    Output("comparison-shift-wrapper", "style"),
    Input("comparison-dropdown", "value"),
    prevent_initial_call=True,
)
def toggle_comparison_shift(comparison):
    if comparison == "shift":
        return {"display": "block", "marginTop": "8px"}
    return {"display": "none"}


@app.callback(
    Output("boxplot",      "figure"),
    Output("stats-table",  "data"),
    Output("status-msg",   "children"),
    Output("report-store", "data"),
    Output("last-updated", "children"),
    Input("run-btn", "n_clicks"),
    State("operator-dropdown",        "value"),
    State("mold-dropdown",            "value"),
    State("date-start",               "value"),
    State("date-end",                 "value"),
    State("options-checklist",        "value"),
    State("comparison-dropdown",      "value"),
    State("comparison-shift-dropdown","value"),
    prevent_initial_call=True,
)
def run_report(n_clicks, emp_numbers, mold, date_start, date_end, options,
               comparison, comparison_shift):
    if not emp_numbers:
        return (build_plotly_boxplot([]), [],
                "Select at least one operator.", None, "")

    full_cycle_only = "full_cycle_only" in (options or [])
    exclude_flagged = "exclude_flagged" in (options or [])

    shared_kwargs = dict(
        mold_name       = mold or None,
        date_start      = date_start,
        date_end        = date_end,
        full_cycle_only = full_cycle_only,
        exclude_flagged = exclude_flagged,
    )

    try:
        conn = get_connection(DB_PATH)

        # Individual operator traces
        frames = []
        for emp_num in emp_numbers:
            df = get_operator_cycle_times(
                conn, employee_number=emp_num, **shared_kwargs
            )
            if not df.empty:
                frames.append(df)

        # Comparison baseline trace(s)
        baseline_frames = []
        if comparison == "all":
            df_all = get_all_cycles(conn, **shared_kwargs)
            if not df_all.empty:
                baseline_frames.append(df_all)
        elif comparison == "shift":
            if comparison_shift:
                df_shift = get_shift_cycle_times(
                    conn, shift=comparison_shift, **shared_kwargs
                )
                if not df_shift.empty:
                    baseline_frames.append(df_shift)

        conn.close()
    except Exception as e:
        return (build_plotly_boxplot([]), [],
                f"Database error: {e}", None, "")

    if not frames and not baseline_frames:
        return (build_plotly_boxplot([]), [],
                "No data found for the selected filters.", None, "")

    # Baselines go first so they render behind individual operators
    fig        = build_plotly_boxplot(baseline_frames + frames,
                                      baseline_count=len(baseline_frames))
    table_rows = build_stats_rows(frames)
    total      = sum(len(df) for df in frames)
    n_ops      = len(frames)
    status     = f"{total} cycles across {n_ops} operator(s)."
    if baseline_frames:
        status += f" Showing {comparison} baseline."
    timestamp  = f"Last run: {dt.datetime.now().strftime('%H:%M:%S')}"

    store = {
        "emp_numbers":      emp_numbers,
        "mold":             mold,
        "date_start":       date_start,
        "date_end":         date_end,
        "full_cycle_only":  full_cycle_only,
        "exclude_flagged":  exclude_flagged,
        "comparison":       comparison,
        "comparison_shift": comparison_shift,
    }

    return fig, table_rows, status, store, timestamp


@app.callback(
    Output("pdf-download", "data"),
    Input("pdf-btn", "n_clicks"),
    State("report-store", "data"),
    prevent_initial_call=True,
)
def export_pdf(n_clicks, store):
    if not store:
        return None
    try:
        conn = get_connection(DB_PATH)

        shared_kwargs = dict(
            mold_name       = store["mold"] or None,
            date_start      = store["date_start"],
            date_end        = store["date_end"],
            full_cycle_only = store["full_cycle_only"],
            exclude_flagged = store["exclude_flagged"],
        )

        frames = []
        for emp_num in store["emp_numbers"]:
            df = get_operator_cycle_times(
                conn, employee_number=emp_num, **shared_kwargs
            )
            if not df.empty:
                frames.append(df)

        comparison = store.get("comparison", "none")
        if comparison == "all":
            df_all = get_all_cycles(conn, **shared_kwargs)
            if not df_all.empty:
                frames.insert(0, df_all)
        elif comparison == "shift" and store.get("comparison_shift"):
            df_shift = get_shift_cycle_times(
                conn, shift=store["comparison_shift"], **shared_kwargs
            )
            if not df_shift.empty:
                frames.insert(0, df_shift)

        conn.close()

        pdf_bytes = generate_pdf_bytes(
            frames,
            date_start  = store["date_start"],
            date_end    = store["date_end"],
            mold_filter = store["mold"],
        )
        filename = f"cycle_report_{dt.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        return dcc.send_bytes(pdf_bytes, filename)
    except Exception as e:
        print(f"PDF export error: {e}")
        return None


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
    # app.run(debug=True, host="0.0.0.0", port=8050)
