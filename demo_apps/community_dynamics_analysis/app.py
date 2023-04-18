import dash
from dash import html
from components.network_graph.network_graph_layout import network_graph_layout
from components.plots.cardinality_by_type import card_layout
from components.plots.promotions_demotions import promo_demo_layout
from components.plots.avg_core_intervals import avg_intervals_layout
from components.sidebar.sidebar_layout import sidebar_layout
from components.sidebar import sidebar_callbacks
from components.network_graph import network_graph_callbacks

app = dash.Dash(__name__)
app.title = "Community Dynamics Analysis Dashboard"

plots_layout = html.Div(
        className="column",
        style={"flex": "33%"},
        children=[ 
            card_layout,
            promo_demo_layout, 
            avg_intervals_layout
        ]
    )

app.layout = html.Div(
    className="container",
    style={
        "display": "flex",
        "justify-content": "space-between"},
    children=[
        network_graph_layout,
        plots_layout,
        sidebar_layout
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True)


    