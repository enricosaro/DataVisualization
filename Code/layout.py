from dash import dcc, html
import dash_bootstrap_components as dbc


# --- Intro ---

def make_intro():
    """
    Intro section describing the data source and what the dashboard shows.
    """
    description_text = """
### Inside Airbnb Gent Dashboard

This dashboard visualizes Airbnb listings for the city of Ghent.

Data source: https://insideairbnb.com/get-the-data/

You can:  
• Filter by room type, price range, and minimum nights  
• Explore listings on the interactive map  
• See how filters change price distribution and room type composition
"""
    return dcc.Markdown(children=description_text.strip())


# --- Controls ---

def make_filter_controls():
    """
    Filter controls used by callbacks (ids must match callbacks.py):
    - room-type (multi dropdown)
    - price-range (range slider)
    - min-nights (slider)
    """
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H3("Filters"),
                    html.Label("Room type"),
                    dcc.Dropdown(
                        id="room-type",
                        options=[
                            {"label": "Entire home/apt", "value": "Entire home/apt"},
                            {"label": "Private room", "value": "Private room"},
                            {"label": "Shared room", "value": "Shared room"},
                            {"label": "Hotel room", "value": "Hotel room"},
                            {"label": "Unknown", "value": "Unknown"},
                        ],
                        value=[
                            "Entire home/apt",
                            "Private room",
                            "Shared room",
                            "Hotel room",
                            "Unknown",
                        ],
                        multi=True,
                        clearable=False,
                    ),
                    html.Br(),
                    html.Label("Price range (€)"),
                    dcc.RangeSlider(
                        id="price-range",
                        min=0,
                        max=500,
                        step=10,
                        value=[0, 400],
                        tooltip={"placement": "bottom", "always_visible": False},
                        marks={0: "0", 100: "100", 200: "200", 300: "300", 400: "400", 500: "500"},
                    ),
                    html.Br(),
                    html.Label("Minimum nights (≥)"),
                    dcc.Slider(
                        id="min-nights",
                        min=1,
                        max=30,
                        step=1,
                        value=1,
                        tooltip={"placement": "bottom", "always_visible": False},
                        marks={1: "1", 7: "7", 14: "14", 21: "21", 30: "30"},
                    ),
                    html.Br(),
                    html.Small("Adjust filters to see how affordability and supply mix change."),
                ],
                md=6,
            ),
        ],
        className="mb-3",
    )


# --- Map ---
def make_map_block():
    """
    Interactive map block. The Graph id must be 'listings-map' to match callbacks.py.
    """
    return dbc.Row(
        dbc.Col(
            [
                html.H3("Interactive map"),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Small("Use box/lasso to select points. Click 'Clear map selection' to reset."),
                            width="auto"
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Clear map selection",
                                id="clear-selection",
                                color="secondary",
                                outline=True,
                                className="ms-3",   # margin-left smart spacing
                                title="Reset any box/lasso selection on the map",
                            ),
                            width="auto"
                        ),
                    ],
                    align="center",
                    className="mb-2",
                ),
                dcc.Graph(id="listings-map", style={"width": "100%", "height": "520px"}),
            ],
            md=12,
        ),
        className="mb-4",
    )


# --- Charts ---

def make_summary_charts():
    """
    Two summary charts under the map:
    - price-histogram: price distribution
    - roomtype-composition: room type composition
    """
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H3("Price distribution"),
                    # Figure provided by callbacks; keep id consistent with callbacks.py
                    dcc.Graph(id="price-histogram"),
                ],
                md=6,
                className="mb-4",
            ),
            dbc.Col(
                [
                    html.H3("Room type composition"),
                    dcc.Graph(id="roomtype-composition"),
                ],
                md=6,
                className="mb-4",
            ),
        ],
        className="mb-5",
    )


# --- Page layout ---

def get_app_layout():
    """
    Single-page layout:
    - Title
    - Intro
    - Filters
    - Map
    - Charts
    - Footer with data source
    """
    return dbc.Container(
        [
            html.H1("Inside Airbnb Gent", className="my-3"),
            make_intro(),
            html.Hr(),
            make_filter_controls(),
            make_map_block(),
            make_summary_charts(),
            html.Footer(
                dcc.Markdown("Data source: Inside Airbnb https://insideairbnb.com/get-the-data/"),
                className="my-4",
            ),
        ],
        fluid=True,
    )