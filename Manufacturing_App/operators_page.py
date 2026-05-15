"""
operators_page.py

Dash page for operator management:
  - Add a new operator (number selection prevents choosing active numbers)
  - Retire an operator (requires confirmation before freeing the number)
  - Generate double-sided ID card PDFs for selected operators

Import this module in app.py and register its layout and callbacks.
"""

import datetime as dt

import dash
from dash import dcc, html, dash_table, Input, Output, State, ctx
import dash_bootstrap_components as dbc

import yaml

from analytics import get_connection
import id_cards
from nav import navbar

CONFIG_FILE = 'config_vars.yaml'

with open(CONFIG_FILE, 'r') as file:
    config_data = yaml.safe_load(file)
    DB_PATH = config_data['db_path']

# DB_PATH = "C:/Users/Ryan.Larson/Documents/Rockwell Manufacturing Database/manufacturing.db"

# Paths needed for card generation.
# Update these to match your actual file locations on the server.
TEMPLATE_PATH = "assets/Portrait_white_ID.png"
FONT_PATH     = "assets/Roboto-Black.ttf"

SHIFTS = ["Day", "Swing", "Graveyard"]


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
    "padding": "20px",
    "marginBottom": "16px",
}

INPUT_STYLE = {
    "width": "100%", "padding": "7px 10px",
    "fontFamily": "Inter, sans-serif", "fontSize": "13px",
    "color": "#1e293b", "backgroundColor": "#ffffff",
    "border": "1px solid #cbd5e1", "borderRadius": "6px",
    "outline": "none",
}

BTN_PRIMARY = {
    "padding": "9px 20px", "backgroundColor": "#2563eb",
    "color": "#ffffff", "border": "none", "borderRadius": "6px",
    "fontFamily": "Inter, sans-serif", "fontWeight": "600",
    "fontSize": "13px", "cursor": "pointer", "marginTop": "8px",
}

BTN_DANGER = {
    "padding": "9px 20px", "backgroundColor": "#dc2626",
    "color": "#ffffff", "border": "none", "borderRadius": "6px",
    "fontFamily": "Inter, sans-serif", "fontWeight": "600",
    "fontSize": "13px", "cursor": "pointer", "marginTop": "8px",
}

BTN_SECONDARY = {
    "padding": "9px 20px", "backgroundColor": "#ffffff",
    "color": "#2563eb", "border": "1px solid #2563eb",
    "borderRadius": "6px", "fontFamily": "Inter, sans-serif",
    "fontWeight": "600", "fontSize": "13px", "cursor": "pointer",
    "marginTop": "8px",
}


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    conn       = get_connection(DB_PATH)
    active_ops = id_cards.get_active_operators(conn)
    available  = id_cards.get_available_numbers(conn)
    conn.close()

    active_options = [
        {"label": f"{op['name']} ({op['employee_number']})", "value": op["id"]}
        for op in active_ops
    ]

    number_options = [
        {"label": str(n), "value": n}
        for n in available
    ]

    return html.Div(
        style={"backgroundColor": "#f1f5f9", "minHeight": "100vh",
               "fontFamily": "Inter, sans-serif"},
        children=[

            navbar("Operator Management"),

            html.Div(style={"padding": "20px 28px"}, children=[
                dbc.Row([

                    # Left column
                    dbc.Col(width=5, children=[

                        # ── Add operator ──
                        html.Div(style=PANEL, children=[
                            html.Label("Add New Operator", style={
                                **LABEL,
                                "fontSize": "13px",
                                "color": "#1e293b",
                                "textTransform": "none",
                                "fontWeight": "600",
                                "marginBottom": "14px",
                            }),

                            html.Label("Name", style=LABEL),
                            dcc.Input(
                                id="new-op-name",
                                type="text",
                                placeholder="Full name",
                                debounce=True,
                                style=INPUT_STYLE,
                            ),

                            html.Div(style={"marginTop": "12px"}, children=[
                                html.Label("Employee Number", style=LABEL),
                                dcc.Dropdown(
                                    id="new-op-number",
                                    options=number_options,
                                    placeholder="Select available number...",
                                    searchable=True,
                                ),
                            ]),

                            html.Div(style={"marginTop": "12px"}, children=[
                                html.Label("Shift", style=LABEL),
                                dcc.Dropdown(
                                    id="new-op-shift",
                                    options=[{"label": s, "value": s}
                                             for s in SHIFTS],
                                    placeholder="Select shift...",
                                    clearable=False,
                                ),
                            ]),

                            html.Div(style={"marginTop": "12px"}, children=[
                                html.Label("Start Date", style=LABEL),
                                dcc.Input(
                                    id="new-op-date",
                                    type="text",
                                    value=dt.date.today().isoformat(),
                                    placeholder="YYYY-MM-DD",
                                    debounce=True,
                                    style=INPUT_STYLE,
                                ),
                            ]),

                            html.Button(
                                "Add Operator",
                                id="add-op-btn",
                                style=BTN_PRIMARY,
                            ),

                            html.Div(id="add-op-msg", style={
                                "marginTop": "8px", "fontSize": "12px",
                                "minHeight": "18px",
                            }),
                        ]),

                        # ── Retire operator ──
                        html.Div(style=PANEL, children=[
                            html.Label("Retire Operator", style={
                                **LABEL,
                                "fontSize": "13px",
                                "color": "#1e293b",
                                "textTransform": "none",
                                "fontWeight": "600",
                                "marginBottom": "14px",
                            }),

                            html.Label("Operator", style=LABEL),
                            dcc.Dropdown(
                                id="retire-op-select",
                                options=active_options,
                                placeholder="Select operator to retire...",
                                searchable=True,
                            ),

                            html.Div(style={"marginTop": "12px"}, children=[
                                html.Label("End Date", style=LABEL),
                                dcc.Input(
                                    id="retire-op-date",
                                    type="text",
                                    value=dt.date.today().isoformat(),
                                    placeholder="YYYY-MM-DD",
                                    debounce=True,
                                    style=INPUT_STYLE,
                                ),
                            ]),

                            # Confirmation section -- hidden until operator selected
                            html.Div(
                                id="retire-confirm-section",
                                style={"display": "none"},
                                children=[
                                    html.Div(style={
                                        "marginTop": "14px",
                                        "padding": "12px",
                                        "backgroundColor": "#fef2f2",
                                        "border": "1px solid #fca5a5",
                                        "borderRadius": "6px",
                                    }, children=[
                                        html.P(
                                            id="retire-confirm-msg",
                                            style={
                                                "margin": "0 0 10px 0",
                                                "fontSize": "13px",
                                                "color": "#991b1b",
                                                "fontWeight": "500",
                                            }
                                        ),
                                        html.Label("Enter authorization password:",
                                                   style={"fontSize": "12px",
                                                          "color": "#7f1d1d",
                                                          "fontWeight": "600",
                                                          "display": "block",
                                                          "marginBottom": "4px"}),
                                        dcc.Input(
                                            id="retire-password-input",
                                            type="password",
                                            placeholder="Password",
                                            debounce=True,
                                            style={
                                                "width": "100%",
                                                "padding": "7px 10px",
                                                "fontFamily": "Inter, sans-serif",
                                                "fontSize": "13px",
                                                "color": "#1e293b",
                                                "backgroundColor": "#ffffff",
                                                "border": "1px solid #fca5a5",
                                                "borderRadius": "6px",
                                                "outline": "none",
                                                "marginBottom": "8px",
                                            },
                                        ),
                                        html.Div(
                                            id="retire-password-msg",
                                            style={"fontSize": "11px",
                                                   "color": "#dc2626",
                                                   "minHeight": "16px",
                                                   "marginBottom": "6px"},
                                        ),
                                    ]),

                                    html.Button(
                                        "Retire Operator",
                                        id="retire-op-btn",
                                        style={**BTN_DANGER,
                                               "opacity": "0.4",
                                               "cursor": "not-allowed"},
                                        disabled=True,
                                    ),
                                ],
                            ),

                            html.Div(id="retire-op-msg", style={
                                "marginTop": "8px", "fontSize": "12px",
                                "minHeight": "18px",
                            }),
                        ]),
                    ]),

                    # Right column
                    dbc.Col(width=7, children=[

                        # ── Generate ID cards ──
                        html.Div(style=PANEL, children=[
                            html.Label("Generate ID Cards", style={
                                **LABEL,
                                "fontSize": "13px",
                                "color": "#1e293b",
                                "textTransform": "none",
                                "fontWeight": "600",
                                "marginBottom": "14px",
                            }),

                            html.Label("Select Operators", style=LABEL),
                            dcc.Dropdown(
                                id="card-op-select",
                                options=active_options,
                                multi=True,
                                placeholder="Select operators to generate cards for...",
                            ),

                            html.Div(style={
                                "display": "flex", "gap": "10px",
                                "marginTop": "12px",
                            }, children=[
                                html.Button(
                                    "Select All Active",
                                    id="card-select-all-btn",
                                    style=BTN_SECONDARY,
                                ),
                                html.Button(
                                    "Generate PDF",
                                    id="card-generate-btn",
                                    style=BTN_PRIMARY,
                                ),
                            ]),

                            dcc.Download(id="card-pdf-download"),

                            html.Div(id="card-gen-msg", style={
                                "marginTop": "8px", "fontSize": "12px",
                                "color": "#64748b", "minHeight": "18px",
                            }),
                        ]),

                        # ── Active operators table ──
                        html.Div(style=PANEL, children=[
                            html.Label("Active Operators", style={
                                **LABEL,
                                "fontSize": "13px",
                                "color": "#1e293b",
                                "textTransform": "none",
                                "fontWeight": "600",
                                "marginBottom": "14px",
                            }),
                            dash_table.DataTable(
                                id="active-ops-table",
                                columns=[
                                    {"name": "Name",       "id": "name"},
                                    {"name": "Emp #",      "id": "employee_number"},
                                    {"name": "Shift",      "id": "shift"},
                                    {"name": "Start Date", "id": "active_from"},
                                ],
                                data=[
                                    {
                                        "name":            op["name"],
                                        "employee_number": op["employee_number"],
                                        "shift":           op["shift"],
                                        "active_from":     op["active_from"],
                                    }
                                    for op in active_ops
                                ],
                                style_table={"overflowX": "auto"},
                                style_header={
                                    "backgroundColor": "#f1f5f9",
                                    "color": "#475569",
                                    "fontWeight": "600",
                                    "fontSize": "12px",
                                    "border": "1px solid #e2e8f0",
                                    "padding": "10px 12px",
                                },
                                style_cell={
                                    "backgroundColor": "#ffffff",
                                    "color": "#1e293b",
                                    "fontSize": "13px",
                                    "border": "1px solid #e2e8f0",
                                    "padding": "8px 12px",
                                    "textAlign": "left",
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

            # Stores for inter-callback state
            dcc.Store(id="ops-page-refresh", data=0),
        ]
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def register_callbacks(app):

    # Show/hide and populate the retirement confirmation section
    @app.callback(
        Output("retire-confirm-section", "style"),
        Output("retire-confirm-msg",     "children"),
        Input("retire-op-select", "value"),
        prevent_initial_call=True,
    )
    def show_retire_confirm(operator_id):
        if not operator_id:
            return {"display": "none"}, ""

        conn = get_connection(DB_PATH)
        ops  = id_cards.get_active_operators(conn)
        conn.close()

        op = next((o for o in ops if o["id"] == operator_id), None)
        if not op:
            return {"display": "none"}, ""

        msg = (
            f"You are about to retire {op['name']} "
            f"(employee #{op['employee_number']}). "
            f"Their number will become available for reassignment."
        )
        return {"display": "block"}, msg


    # Enable retire button only when correct password is entered
    @app.callback(
        Output("retire-op-btn",       "disabled"),
        Output("retire-op-btn",       "style"),
        Output("retire-password-msg", "children"),
        Input("retire-password-input","value"),
        prevent_initial_call=True,
    )
    def toggle_retire_btn(password):
        with open(CONFIG_FILE, 'r') as f:
            cfg = yaml.safe_load(f)
        correct = str(cfg.get("retire_password", ""))

        if not password:
            return True, {**BTN_DANGER, "opacity": "0.4",
                          "cursor": "not-allowed"}, ""
        if password == correct:
            return False, BTN_DANGER, ""
        return True, {**BTN_DANGER, "opacity": "0.4",
                      "cursor": "not-allowed"}, "Incorrect password."


    # Add operator
    @app.callback(
        Output("add-op-msg",        "children"),
        Output("add-op-msg",        "style"),
        Output("ops-page-refresh",  "data"),
        Input("add-op-btn", "n_clicks"),
        State("new-op-name",   "value"),
        State("new-op-number", "value"),
        State("new-op-shift",  "value"),
        State("new-op-date",   "value"),
        State("ops-page-refresh", "data"),
        prevent_initial_call=True,
    )
    def add_operator(n_clicks, name, emp_num, shift, active_from, refresh):
        if not all([name, emp_num, shift, active_from]):
            return ("Please fill in all fields.",
                    {"marginTop": "8px", "fontSize": "12px",
                     "color": "#dc2626", "minHeight": "18px"},
                    refresh)
        try:
            conn = get_connection(DB_PATH, read_only=False)
            id_cards.add_operator(conn, int(emp_num), name.strip(),
                                  active_from, shift)
            conn.close()
            return (
                f"✓ {name} added as operator #{emp_num}.",
                {"marginTop": "8px", "fontSize": "12px",
                 "color": "#16a34a", "minHeight": "18px"},
                (refresh or 0) + 1,
            )
        except Exception as e:
            return (
                str(e),
                {"marginTop": "8px", "fontSize": "12px",
                 "color": "#dc2626", "minHeight": "18px"},
                refresh,
            )


    # Retire operator
    @app.callback(
        Output("retire-op-msg",       "children"),
        Output("retire-op-msg",       "style"),
        Output("ops-page-refresh",    "data", allow_duplicate=True),
        Input("retire-op-btn", "n_clicks"),
        State("retire-op-select",      "value"),
        State("retire-op-date",        "value"),
        State("retire-password-input", "value"),
        State("ops-page-refresh",      "data"),
        prevent_initial_call=True,
    )
    def retire_operator(n_clicks, operator_id, active_to, password, refresh):
        # Re-check password server-side (button enable/disable is UI-only)
        with open(CONFIG_FILE, 'r') as f:
            cfg = yaml.safe_load(f)
        correct = str(cfg.get("retire_password", ""))

        if password != correct:
            return ("Incorrect password.",
                    {"marginTop": "8px", "fontSize": "12px",
                     "color": "#dc2626", "minHeight": "18px"},
                    refresh)
        if not operator_id or not active_to:
            return ("Please select an operator and end date.",
                    {"marginTop": "8px", "fontSize": "12px",
                     "color": "#dc2626", "minHeight": "18px"},
                    refresh)
        try:
            conn = get_connection(DB_PATH, read_only=False)
            id_cards.retire_operator(conn, operator_id, active_to)
            conn.close()
            return (
                "✓ Operator retired successfully.",
                {"marginTop": "8px", "fontSize": "12px",
                 "color": "#16a34a", "minHeight": "18px"},
                (refresh or 0) + 1,
            )
        except Exception as e:
            return (
                str(e),
                {"marginTop": "8px", "fontSize": "12px",
                 "color": "#dc2626", "minHeight": "18px"},
                refresh,
            )


    # Select all active operators for card generation
    @app.callback(
        Output("card-op-select", "value"),
        Input("card-select-all-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def select_all_for_cards(n_clicks):
        conn = get_connection(DB_PATH)
        ops  = id_cards.get_active_operators(conn)
        conn.close()
        return [op["id"] for op in ops]


    # Generate ID card PDF
    @app.callback(
        Output("card-pdf-download", "data"),
        Output("card-gen-msg",      "children"),
        Input("card-generate-btn", "n_clicks"),
        State("card-op-select",    "value"),
        prevent_initial_call=True,
    )
    def generate_cards(n_clicks, operator_ids):
        if not operator_ids:
            return None, "Select at least one operator."

        try:
            from PIL import Image
            template = Image.open(TEMPLATE_PATH)

            conn = get_connection(DB_PATH)
            ops  = id_cards.get_active_operators(conn)
            conn.close()

            # Build lookup by operators.id -> (employee_number, name)
            id_to_empnum = {op["id"]: op["employee_number"] for op in ops}
            id_to_name   = {op["id"]: op["name"]            for op in ops}

            emp_numbers = [id_to_empnum[oid] for oid in operator_ids
                           if oid in id_to_empnum]
            names       = {id_to_empnum[oid]: id_to_name[oid]
                           for oid in operator_ids if oid in id_to_empnum}

            if not emp_numbers:
                return None, "No valid operators found."

            pdf_bytes = id_cards.generate_operator_pdf(
                emp_numbers, names, template, FONT_PATH
            )

            filename = (
                f"operator_cards_"
                f"{dt.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            )
            return dcc.send_bytes(pdf_bytes, filename), \
                   f"✓ PDF generated for {len(emp_numbers)} operator(s)."

        except Exception as e:
            return None, f"Error generating PDF: {e}"
