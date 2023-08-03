from dash import dcc, html
import dash_bootstrap_components as dbc

network_graph = html.Div(
        className="graph-container",
        children=[
            html.Div(
                style={"position": "relative", "padding-bottom": "100%"},
                children=[
                    dcc.Graph(
                        id="graph-animation",
                        style={"position": "absolute", "width": "100%", "height": "100%"}
                    )
                ]
            ),
            html.Div([
                html.H4([
                    html.Span(
                        "[i]",
                        id="graph-tooltip",
                        style={"cursor": "pointer", "font-size": "15px", "margin-left": "20px", "color": "gray"},
                    ),
                ]),
                dbc.Tooltip(
                    "The network graph represents the contributor connections at a given time interval. Each node represents a contributor (🔴 Core 🔵 Peripheral). The edges represent the connections between contributors. The more central a node is, the more a given contributor has contributed to the project.",
                    target="graph-tooltip",
                    placement="top-start",
                    style={"background-color": "white", "color": "#000", "max-width": "750px"}
                ),
            ]),
            dcc.Interval(id='animation-interval', interval=1000, disabled=True)  # Disabled by default
        ]
    )

slider_layout = html.Div(
        style={"margin-top": "20px"},
        children=[
            dcc.RangeSlider(
                id="graph-slider",
                value=[0, 1],
                marks={},
                step=1
            ),
            html.Button('▶', id='play-button', n_clicks=0, style={'margin-left': '10px', 'margin-right': '10px'}),
            html.Button('⏸', id='pause-button', n_clicks=0),
        ]
    )

network_graph_layout = html.Div(
    className="main-content",
    style={"flex": "50%"},
    children=[
        html.H1("Community Dynamics Analysis Dashboard"),
        html.Div(
            children=[
                network_graph,
                slider_layout,
            ],
            style={"display": "flex", "flex-direction": "column"},
        ),
    ]
)