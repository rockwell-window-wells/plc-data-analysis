"""
nav.py

Shared navigation header for all pages in the Rockwell Manufacturing dashboard.

Usage:
    from nav import navbar
    ...
    html.Div([
        navbar("Operator Performance"),
        # page body
    ])

The active page title is highlighted in white; all other nav links are shown
in a muted grey and highlight on hover. The "ROCKWELL MANUFACTURING" wordmark
is always shown on the left.
"""

from dash import dcc, html


# ---------------------------------------------------------------------------
# Nav pages registry
# Each entry: (label, href)
# ---------------------------------------------------------------------------

PAGES = [
    ("Operator Performance", "/"),
    ("Cycle Analysis",       "/cycle-analysis"),
    ("Resin Analysis",       "/resin-analysis"),
    ("Operator Management",  "/operators"),
]


def navbar(active_title: str) -> html.Div:
    """
    Return the shared top navigation bar.

    Parameters
    ----------
    active_title : str
        The title of the current page, used to highlight the active nav link
        and display it as the page heading. Must match one of the labels in
        PAGES exactly.
    """
    nav_links = []
    for label, href in PAGES:
        is_active = label == active_title
        if is_active:
            # Active page: shown as the page title, not a clickable link
            nav_links.append(
                html.Span(label, style={
                    "fontSize": "13px",
                    "fontWeight": "600",
                    "color": "#f8fafc",
                    "fontFamily": "Inter, sans-serif",
                    "cursor": "default",
                })
            )
        else:
            nav_links.append(
                dcc.Link(label, href=href, style={
                    "fontSize": "13px",
                    "fontWeight": "400",
                    "color": "#94a3b8",
                    "fontFamily": "Inter, sans-serif",
                    "textDecoration": "none",
                    "transition": "color 0.15s",
                })
            )

    # Separator dots between links
    separated = []
    for i, link in enumerate(nav_links):
        separated.append(link)
        if i < len(nav_links) - 1:
            separated.append(
                html.Span("·", style={
                    "color": "#475569",
                    "fontSize": "13px",
                    "fontFamily": "Inter, sans-serif",
                })
            )

    return html.Div(
        style={
            "backgroundColor": "#1e293b",
            "padding": "14px 28px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
        },
        children=[
            # Left: wordmark + page title
            html.Div([
                html.Span("ROCKWELL MANUFACTURING", style={
                    "fontSize": "11px",
                    "fontWeight": "600",
                    "color": "#94a3b8",
                    "letterSpacing": "0.15em",
                    "fontFamily": "Inter, sans-serif",
                }),
                html.H1(active_title, style={
                    "margin": "2px 0 0 0",
                    "fontSize": "20px",
                    "fontWeight": "500",
                    "color": "#f8fafc",
                    "fontFamily": "Inter, sans-serif",
                }),
            ]),

            # Right: nav links
            html.Div(
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "12px",
                },
                children=separated,
            ),
        ],
    )
