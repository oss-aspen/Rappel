from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback 
import plotly.graph_objs as go
from data_utils.queries import fetch_data
from components.plots.plots_helper import get_plot_data, add_trace

#layout
card_layout =  html.Div(
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

# plot callback
@callback(
    [
        Output('contributor-type-cardinality', 'figure')
    ],
    [
        Input('cardinality-checklist', 'value'),
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
def card_plot(card_checks, n_clicks, repo_org, repo_name, marks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold_type, threshold_value):
    """
    Generate a trend plot for cardinality by contributor type.

    Args:
    -----
        card_checks (list): A list containing strings representing the selected contributor types to 
                            display on the plot (e.g., 'core', 'peripheral', 'new', 'all time').
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
        go.Figure: A Plotly Figure representing the plot for cardinality by contributor type.
    """
    marks = list(marks.values())
    threshold = [threshold_type, threshold_value]
    data = fetch_data(repo_org, repo_name)
    plot_df = get_plot_data(data, marks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold)
 
    fig_data = []
    # add traces based on user selection
    for c in card_checks: 
        if c == "core":
            core_trace = add_trace(plot_df['core'], c, 'red', marks)
            fig_data.append(core_trace)
        if c == "peripheral": 
            per_trace = add_trace(plot_df['peripheral'], c, 'blue', marks)
            fig_data.append(per_trace)
        if c == "new":
            new_trace = add_trace(plot_df['new'], c, 'green', marks)
            fig_data.append(new_trace)
        if c == "all time":
            all_time_trace = add_trace(plot_df['all_time'], c, 'orange', marks)
            fig_data.append(all_time_trace)

    layout =  dict(
        yaxis = dict(title = 'Contributor Count'),
        xaxis = dict(title = 'Intervals'), 
        margin = {"t": 0}
    )

    return [go.Figure(fig_data, layout)]

