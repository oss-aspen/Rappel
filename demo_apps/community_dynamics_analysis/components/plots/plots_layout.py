from dash import dcc, html
import dash_bootstrap_components as dbc

cardinality =  html.Div(
    className="graph-container",
    children=[
        html.Div([
            html.H4([
                html.Span(
                    "[i]",
                    id="card-tooltip",
                    style={"cursor": "pointer", "font-size": "15px", "margin-left": "20px", "margin-right": "5px", "margin-top": "50px","color": "grey"},
                ),
                "Cardinality by Contributor Type"
            ]),
            dbc.Tooltip(
                "This graph captures the trend of counts of core, peripheral, and new developers at each interval in the specified time frame. ",
                target="card-tooltip",
                placement="bottom-start",
                style={"background-color": "white", "color": "#000", "max-width": "500px"}
            ),
        ]),
        dcc.Graph(id="contributor-type-cardinality", style={'height': '300px'}),
        dcc.Checklist(
            id="cardinality-checklist",
            options=["core", "peripheral", "new", "all time"],
            value=["core", "peripheral", "new", "all time"],
            inline=True,
            style = {"padding-left": "30px"}
        )
    ]
)
                
promo_demo = html.Div(
    className="graph-container",
    children=[
        html.Div([
            html.H4([
                html.Span(
                    "[i]",
                    id="promo-demo-tooltip",
                    style={"cursor": "pointer", "font-size": "15px", "margin-left": "20px", "margin-right": "5px", "margin-top": "50px","color": "grey"},
                ),
                "Contributor Promotions and Demotions"
            ]),
            dbc.Tooltip(
                "This graph captures the trend of contributors switching from peripheral to core type (promotion) and from core to peripheral (demotion).",
                target="promo-demo-tooltip",
                placement="bottom-start",
                style={"background-color": "white", "color": "#000", "max-width": "500px"}
            ),
        ]),
        dcc.Graph(id="promotions-demotions", style={'height': '300px'}),
        dcc.Checklist(
            id="promo-demo-checklist",
            options=["promotions", "demotions"],
            value=["promotions", "demotions"],
            inline=True,
            style = {"padding-left": "30px"}
        )
    ]
)

avg_intervals = html.Div(
    className="graph-container",
    children=[
        html.Div([
            html.H4([
                html.Span(
                    "[i]",
                    id="avg-int-tooltip",
                    style={"cursor": "pointer", "font-size": "15px", "margin-left": "20px", "margin-right": "5px", "margin-top": "50px","color": "grey"},
                ),
                "Average Intervals Served as Core"
            ]),
            dbc.Tooltip(
                "This graph captures the trend of of the average number of time intervals that the core contributors have served as core.",
                target="avg-int-tooltip",
                placement="bottom-start",
                style={"background-color": "white", "color": "#000", "max-width": "500px"}
            ),
        ]),
        dcc.Graph(id="average-intervals", style={'height': '300px'})
    ]
)


plots_layout = html.Div(
        className="column",
        style={"flex": "33%"},
        children=[ 
            cardinality,
            promo_demo, 
            avg_intervals
        ]
    )
