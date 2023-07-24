import dash
from dash import html, callback
from dashboard.network_graph import network_graph_layout
from dashboard.plots import plots_layout
from dashboard.sidebar import sidebar_layout

app = dash.Dash(__name__)
app.title = "Community Dynamics Analysis Dashboard"


app.layout = html.Div(
    className="container",
    style={
        "display": "flex",
        "flex-direction": "row",
        "justify-content": "space-between"
    },
    children=[
        network_graph_layout,
        plots_layout,
        sidebar_layout
    ]
)
