import dash
from dash import html
from components.network_graph.network_graph_layout import network_graph_layout
from components.plots.plots_layout import plots_layout
from components.sidebar.sidebar_layout import sidebar_layout
from components.sidebar import sidebar_callbacks
from components.network_graph import network_graph_callbacks
from components.plots import plots_callbacks

app = dash.Dash(__name__)
app.title = "Community Dynamics Analysis Dashboard"

app.layout = html.Div(
    className="container",
    style={
        "display": "flex",
        "flex-direction": "row",
        "justify-content": "space-between"},
    children=[
        network_graph_layout,
        plots_layout,
        sidebar_layout
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True)


    