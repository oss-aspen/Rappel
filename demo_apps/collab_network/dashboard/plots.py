import numpy as np
from dash import dcc, html, Dash, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import networkx as nx
from collections import Counter
from .queries import fetch_data
from .graph_helper import get_intervals, find_threshold, build_graph
import dashboard.app as app


#------------------------------------------------------ COLLECT PLOT DATA ------------------------------------------------------ 

def get_plot_data(data, start_year, start_month, end_year, end_month, interval, cmt_weight, ism_weight, pr_weight, prm_weight, threshold): 
    """
        Loops through each interval frame of the network graph and stores data for plots
    """
    global total_frames, promo_list, demo_list, core, peripheral, new, all_time, avg_intervals

    #initialize sets/lists to populate plot data
    promo_list = []
    demo_list = []
    core = []
    peripheral = []
    new = []
    all_time = []
    avg_intervals = {}

    # calculate the total number of frames
    total_frames = ((end_year - start_year) * 12 + (end_month - start_month)) // interval

    for frame in range(total_frames): 
        update_graph(frame, start_year, start_month, interval, data, cmt_weight, ism_weight, pr_weight, prm_weight, threshold)

    return core, peripheral, new, all_time, promo_list, demo_list, avg_intervals

def update_graph(frame, start_year, start_month, interval, data, cmt_weight, ism_weight, pr_weight, prm_weight, threshold):
    # update the graph for each frame and store values for plots
    global snap_start_year, snap_start_month, last_nodes, prev_nodes, prev_core, prev_peripheral, core_intervals

    if frame == 0:
        snap_start_year = start_year
        snap_start_month = start_month

    snap_end_month = snap_start_month + interval - 1
    snap_end_year = snap_start_year
    if snap_end_month > 12:
        snap_end_month -= 12
        snap_end_year += 1

    # add nodes and edges to the graph based on the snapshot data
    G = build_graph(data, snap_start_month, snap_start_year, snap_end_month, snap_end_year, cmt_weight, ism_weight, pr_weight, prm_weight)

    pagerank_scores = nx.pagerank(G)

    threshold_score = find_threshold(np.array(list(pagerank_scores.values())), threshold)

    if frame == 0:
        prev_nodes, last_nodes, prev_peripheral, prev_core, core_intervals = init_sets(G)

    node_colors = ['r' if pagerank_scores[n] >= threshold_score else 'b' if n in prev_nodes else 'y' for n in G.nodes()]
    core_nodes = set([node for node in set(G.nodes()) if pagerank_scores[node] >= threshold_score])
    peripheral_nodes = set([node for node in set(G.nodes()) if pagerank_scores[node] < threshold_score])

    # populate core intervals
    for node in core_nodes:
        core_intervals[node] = core_intervals.get(node, 0) + 1

    avg_intervals[frame] = sum(core_intervals[node] for node in core_nodes) / len(core_nodes)

    prev_nodes = prev_nodes | set(G.nodes())
    peripheral_to_core = len(prev_peripheral.intersection(core_nodes))
    core_to_peripheral = len(prev_core.intersection(peripheral_nodes))

    # update the prev_nodes, prev_core, and prev_peripheral variables for the next frame
    last_nodes = set(G.nodes())
    prev_core = core_nodes
    prev_peripheral = peripheral_nodes

    # count contrubutor types (by color)
    counts = Counter(node_colors)
    core.append(counts['r'])
    peripheral.append(counts['b'])
    new.append(counts['y'])
    all_time.append(len(prev_nodes))
    promo_list.append(peripheral_to_core)
    demo_list.append(core_to_peripheral)

    snap_start_year = snap_end_year
    snap_start_month = snap_end_month + 1

    if snap_start_month > 12:
        snap_start_month = 1
        snap_start_year += 1

    if frame == total_frames - 1:
        return None

    return core, peripheral, new, all_time, promo_list, demo_list, avg_intervals

def init_sets(G):
    # initialize sets for first frame
    prev_nodes = set(G.nodes())
    last_nodes = set(G.nodes())
    prev_peripheral = set()
    prev_core = set()
    core_intervals = {}

    return prev_nodes, last_nodes, prev_peripheral, prev_core, core_intervals
#------------------------------------------------------ PLOT TRENDS ------------------------------------------------------ 

def plot_traces(intervals, core, peripheral, new, all_time, peripheral_to_core_list, core_to_peripheral_list, avg_intervals):
    core_trace = go.Scatter(
        y = core,
        x = intervals,
        mode = 'lines',
        name = 'core',
        line = dict(shape = 'linear', color = 'red', width = 2),
        connectgaps = True
        )
    per_trace = go.Scatter(
        y = peripheral,
        x = intervals,
        mode = 'lines',
        name = 'peripheral',
        line = dict(shape = 'linear', color = 'blue', width = 2),
        connectgaps = True
    )
    new_trace = go.Scatter(
        y = new,
        x = intervals,
        mode = 'lines',
        name = 'new',
        line = dict(shape = 'linear', color = 'green', width = 2),
        connectgaps = True
    )
    all_time_trace = go.Scatter(
        y = all_time,
        x = intervals,
        mode = 'lines',
        name = 'all time',
        line = dict(shape = 'linear', color = 'orange', width = 2),
        connectgaps = True
    )
    promo_trace = go.Scatter(
        y = peripheral_to_core_list,
        x = intervals,
        mode = 'lines',
        name = 'promotions',
        line = dict(shape = 'linear', color = 'green', width = 2),
        connectgaps = True
    )
    demo_trace = go.Scatter(
        y = core_to_peripheral_list,
        x = intervals,
        mode = 'lines',
        name = 'demotions',
        line = dict(shape = 'linear', color = 'orange', width = 2),
        connectgaps = True
    )
    avg_int_trace = go.Scatter(
        y = list(avg_intervals.values()),
        x = intervals,
        mode = 'lines',
        name = 'average #intervals',
        line = dict(shape = 'linear', color = 'red', width = 2, dash = 'dot'),
        connectgaps = True
    )
    return core_trace, per_trace, new_trace, all_time_trace, promo_trace, demo_trace, avg_int_trace

def plot_trends(card_checks, core_trace, per_trace, new_trace, all_time_trace, promo_checks, promo_trace, demo_trace, avg_int_trace):
    data1 = []
    for c in card_checks: 
        if c == "core":
            data1.append(core_trace)
        if c == "peripheral": 
            data1.append(per_trace)
        if c == "new":
            data1.append(new_trace)
        if c == "all time":
            data1.append(all_time_trace)

    data2 = []
    for c in promo_checks: 
        if c == "promotions":
            data2.append(promo_trace)
        if c == "demotions":
            data2.append(demo_trace)

    data3 = avg_int_trace
            
    layout1 =  dict(
        yaxis = dict(title = 'Contributor Count'),
        xaxis = dict(title = 'Intervals'), 
        margin = {"t": 0}
    )
    layout2 =  dict(
        yaxis = dict(title = 'Contributor Count'),
        xaxis = dict(title = 'Intervals'),
        margin = {"t": 0}    
    )
    layout3 =  dict(
        yaxis = dict(title = 'Average #intervals as core'),
        xaxis = dict(title = 'Intervals'), 
        margin = {"t": 0}   
    )

    fig1 =  go.Figure(data = data1, layout=layout1)
    fig2 =  go.Figure(data = data2, layout=layout2)
    fig3 =  go.Figure(data = data3, layout=layout3)

    return fig1, fig2, fig3


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
        Input('submit-button', 'n_clicks'),
    ],
    [
        State('repo-org', 'value'),
        State('repo-name', 'value'),
        State('start-year', 'value'),
        State('start-month', 'value'), 
        State('end-year', 'value'),
        State('end-month', 'value'),
        State('interval', 'value'),
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
def plot(n_clicks, repo_org, repo_name, start_year, start_month, end_year, end_month, interval, card_checks, promo_checks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold_type, threshold_value):
    intervals = get_intervals(start_year, start_month, end_year, end_month, interval)
    threshold = [threshold_type, threshold_value]
    data = fetch_data(repo_org, repo_name, ['cmt', 'ism', 'pr', 'prm'])
    core, peripheral, new, all_time, peripheral_to_core_list, core_to_peripheral_list, avg_intervals = get_plot_data(data, start_year, start_month, end_year, end_month, interval, cmt_weight, ism_weight, pr_weight, prm_weight, threshold)
    core_trace, per_trace, new_trace, all_time_trace, promo_trace, demo_trace, avg_int_trace = plot_traces(intervals, core, peripheral, new, all_time, peripheral_to_core_list, core_to_peripheral_list, avg_intervals)
    fig1, fig2, fig3 = plot_trends(card_checks, core_trace, per_trace, new_trace, all_time_trace, promo_checks, promo_trace, demo_trace, avg_int_trace)

    return fig1, fig2, fig3