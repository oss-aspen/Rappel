from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback 
import plotly.graph_objs as go
from data_utils.queries import fetch_data
from components.plots.plots_helper import get_plot_data, add_trace

# layout
avg_intervals_layout = html.Div(
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

# plot callback
@callback(
    [
        Output('average-intervals', 'figure')
    ],
    [
        Input('submit-button', 'n_clicks')
    ],
    [
        State('repo-org', 'value'),
        State('repo-name', 'value'),
        State('graph-slider', 'marks'),
        State('cmt-weight', 'value'), 
        State('ism-weight', 'value'), 
        State('pr-weight', 'value'), 
        State('prm-weight', 'value'),
        State('threshold-dropdown', 'value'), 
        State('number-input', 'value')
    ],
    prevent_initial_call=True
)
def avg_int_plot(n_clicks, repo_org, repo_name, marks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold_type, threshold_value):
    """
    Generate a trend plot for average intervals a core node has served as core at a given interval.

    Args:
    -----
        n_clicks (int): The number of times the submit button has been clicked.
        repo_org (str): The organization name of the repository.
        repo_name (str): The name of the repository.
        marks (list): A list of formatted date strings representing the slider marks.
        cmt_weight, ism_weight, pr_weight, prm_weight (float): The weights to assign to edges in 
                                                               the graph based on event type.
        threshold_type (str): The selected threshold type for differentiating core and peripheral nodes 
                              ('elbow', 'percentage', or 'number').
        threshold_value (float): The selected threshold value for threshold calculation.

    Returns:
    --------
        go.Figure: A Plotly Figure representing the plot for average intervals as core.
    """
    marks = list(marks.values())
    threshold = [threshold_type, threshold_value]
    data = fetch_data(repo_org, repo_name)
    plot_df = get_plot_data(data, marks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold)

    fig_data = add_trace(plot_df['avg_intervals'], 'average #intervals', 'red', marks)

    layout =  dict(
        yaxis = dict(title = 'Average #intervals as core'),
        xaxis = dict(title = 'Intervals'), 
        margin = {"t": 0}   
    )

    return [go.Figure(fig_data, layout)]
