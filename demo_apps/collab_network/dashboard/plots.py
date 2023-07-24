import numpy as np
import pandas as pd 
from dash import dcc, html, Dash, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import networkx as nx
from collections import Counter
from .queries import fetch_data
from .graph_helper import find_threshold, build_graph
import dashboard.app as app
import datetime as dt


#------------------------------------------------------ COLLECT PLOT DATA ------------------------------------------------------ 

def get_plot_data(data, marks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold): 
    # Loops through each interval frame of the network graph and stores data for plots

    #initialize dataframe to store plot data
    plot_df = pd.DataFrame(columns=['core', 'peripheral', 'new', 'all_time', 'promo_list', 'demo_list', 'avg_intervals'])

    # calculate the total number of frames
    total_frames = len(marks)-1

    for frame in range(total_frames): 
        start_date = dt.datetime.strptime(marks[frame], "%m/%Y")
        end_date = dt.datetime.strptime(marks[frame+1], "%m/%Y")

        # add nodes and edges to the graph based on the snapshot data
        G = build_graph(data, start_date, end_date, cmt_weight, ism_weight, pr_weight, prm_weight)

        pagerank_scores = nx.pagerank(G)
        threshold_score = find_threshold(np.array(list(pagerank_scores.values())), threshold)

        if frame == 0:
            prev_nodes, prev_peripheral, prev_core, core_intervals = init_sets(G)

        node_colors = ['r' if pagerank_scores[n] >= threshold_score else 'b' if n in prev_nodes else 'y' for n in G.nodes()]
        core_nodes = set([node for node in set(G.nodes()) if pagerank_scores[node] >= threshold_score])
        peripheral_nodes = set([node for node in set(G.nodes()) if pagerank_scores[node] < threshold_score])

        # populate core intervals
        for node in core_nodes:
            core_intervals[node] = core_intervals.get(node, 0) + 1
        avg_interval = sum(core_intervals[node] for node in core_nodes) / len(core_nodes)

        prev_nodes = prev_nodes | set(G.nodes())
        peripheral_to_core = len(prev_peripheral.intersection(core_nodes))
        core_to_peripheral = len(prev_core.intersection(peripheral_nodes))

        # update the prev_core, and prev_peripheral variables for the next frame
        prev_core = core_nodes
        prev_peripheral = peripheral_nodes

        # count contrubutor types (by color)
        counts = Counter(node_colors)
        core_count = counts['r']
        peripheral_count = counts['b']
        new_count = counts['y']
        all_time_count = len(prev_nodes)

        # Append the data to the df for this frame
        plot_df.loc[frame] = {
            'core': core_count,
            'peripheral': peripheral_count,
            'new': new_count,
            'all_time': all_time_count,
            'promo_list': peripheral_to_core,
            'demo_list': core_to_peripheral,
            'avg_intervals': avg_interval
        }

    return plot_df

def init_sets(G):
    # initialize sets for first frame
    prev_nodes = set(G.nodes())
    prev_peripheral = set()
    prev_core = set()
    core_intervals = {}

    return prev_nodes, prev_peripheral, prev_core, core_intervals

#------------------------------------------------------ PLOT TRENDS ------------------------------------------------------ 
# cardinality by conributor type
def plot_fig1(marks, df, card_checks):
    core_trace = go.Scatter(
        y = df['core'],
        x = marks,
        mode = 'lines',
        name = 'core',
        line = dict(shape = 'linear', color = 'red', width = 2),
        connectgaps = True
        )
    per_trace = go.Scatter(
        y = df['peripheral'],
        x = marks,
        mode = 'lines',
        name = 'peripheral',
        line = dict(shape = 'linear', color = 'blue', width = 2),
        connectgaps = True
    )
    new_trace = go.Scatter(
        y = df['new'],
        x = marks,
        mode = 'lines',
        name = 'new',
        line = dict(shape = 'linear', color = 'green', width = 2),
        connectgaps = True
    )
    all_time_trace = go.Scatter(
        y = df['all_time'],
        x = marks,
        mode = 'lines',
        name = 'all time',
        line = dict(shape = 'linear', color = 'orange', width = 2),
        connectgaps = True
    )
    data = []
    for c in card_checks: 
        if c == "core":
            data.append(core_trace)
        if c == "peripheral": 
            data.append(per_trace)
        if c == "new":
            data.append(new_trace)
        if c == "all time":
            data.append(all_time_trace)

    layout =  dict(
        yaxis = dict(title = 'Contributor Count'),
        xaxis = dict(title = 'Intervals'), 
        margin = {"t": 0}
    )
    fig =  go.Figure(data, layout)

    return fig

# promotions, demotions
def plot_fig2(marks, df, promo_checks):
    promo_trace = go.Scatter(
        y = df['promo_list'],
        x = marks,
        mode = 'lines',
        name = 'promotions',
        line = dict(shape = 'linear', color = 'green', width = 2),
        connectgaps = True
    )
    demo_trace = go.Scatter(
        y = df['demo_list'],
        x = marks,
        mode = 'lines',
        name = 'demotions',
        line = dict(shape = 'linear', color = 'orange', width = 2),
        connectgaps = True
    )
    data = []
    for c in promo_checks: 
        if c == "promotions":
            data.append(promo_trace)
        if c == "demotions":
            data.append(demo_trace)
    
    layout =  dict(
        yaxis = dict(title = 'Contributor Count'),
        xaxis = dict(title = 'Intervals'),
        margin = {"t": 0}    
    )
    fig =  go.Figure(data, layout)
    
    return fig

# average intervals as core
def plot_fig3(marks, df):  
    data = go.Scatter(
        y = df['avg_intervals'],
        x = marks,
        mode = 'lines',
        name = 'average #intervals',
        line = dict(shape = 'linear', color = 'red', width = 2),
        connectgaps = True
    )

    layout =  dict(
        yaxis = dict(title = 'Average #intervals as core'),
        xaxis = dict(title = 'Intervals'), 
        margin = {"t": 0}   
    )
    fig =  go.Figure(data, layout)

    return fig

#------------------------------------------------------ APP LAYOUT ------------------------------------------------------ 
plots_layout = html.Div(
            className="column",
            style={"flex": "33%"},
            children=[
                html.Div(
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
                ),
                html.Div(
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
                ),
                html.Div(
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
            ]
        )

#------------------------------------------------------ CALLBACKS ------------------------------------------------------ 

@app.callback(
    [
        Output('contributor-type-cardinality', 'figure'),
        Output('promotions-demotions', 'figure'),
        Output('average-intervals', 'figure')
    ],
    [
        Input('submit-button', 'n_clicks')
    ],
    [
        State('repo-org', 'value'),
        State('repo-name', 'value'),
        State('graph-slider', 'marks'),
        State('cardinality-checklist', 'value'),
        State('promo-demo-checklist', 'value'), 
        State('cmt-weight', 'value'), 
        State('ism-weight', 'value'), 
        State('pr-weight', 'value'), 
        State('prm-weight', 'value'),
        State('threshold-dropdown', 'value'), 
        State('number-input', 'value')
    ],
    prevent_initial_call=True
)
def plot(n_clicks, repo_org, repo_name, marks, card_checks, promo_checks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold_type, threshold_value):
    marks = list(marks.values())
    threshold = [threshold_type, threshold_value]
    data = fetch_data(repo_org, repo_name, ['cmt', 'ism', 'pr', 'prm'])
    plot_df = get_plot_data(data, marks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold)
    
    fig1 = plot_fig1(marks, plot_df, card_checks)
    fig2 = plot_fig2(marks, plot_df, promo_checks)
    fig3 = plot_fig3(marks, plot_df)

    return fig1, fig2, fig3