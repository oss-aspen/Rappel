import numpy as np
from dash import dcc, html, Dash, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import matplotlib.pyplot as plt
import networkx as nx
import dashboard.app as app
from dashboard.queries import fetch_data
from dashboard.graph_helper import build_graph, pagerank, find_threshold

plt.switch_backend('Agg') 


#------------------------------------------------------ NETWORK GRAPH ------------------------------------------------------ 

def draw_network(G, slider_value, slider_marks, pagerank_scores, scaled_scores, threshold_score):
    # draw the network graph object
    start_month, start_year = map(int, slider_marks[str(slider_value[0])].split("/"))
    end_month, end_year = map(int, slider_marks[str(slider_value[1])].split("/"))
    fig, ax = plt.subplots(figsize=(20, 20))
    node_colors = ['red' if pagerank_scores[n] >= threshold_score else 'blue' for n in G.nodes()]
    node_sizes = [100 * scaled_scores[node] for node in G.nodes()]
    edge_widths = [G[u][v]['weight'] * 0.1 for u, v in G.edges()]
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, ax=ax)
    nx.draw_networkx_edges(G, pos, width=edge_widths, ax=ax)
    ax.set_title(f"{start_month}/{start_year}-{end_month}/{end_year}", fontsize=30)
    edge_trace, node_trace = draw_traces(G, pos, node_colors)
    fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title=(f"{start_month}/{start_year}-{end_month}/{end_year}"),
                    titlefont_size=20,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    figure = go.Figure(data=fig)

    return figure

def draw_traces(G, pos, node_colors):
    # create edge and node traces for the figure
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text')
    
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append('# of connections: '+str(len(adjacencies[1])))

    node_trace.marker.color = node_colors
    node_trace.text = node_text

    return edge_trace, node_trace

#------------------------------------------------------ APP LAYOUT ------------------------------------------------------ 

network_graph_layout = html.Div(
            className="main-content",
            style={"flex": "50%"},
            children=[
                html.H1("Community Dynamics Analysis Dashboard"),
                html.Div(
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
                                "The network graph represents the contributor connections at a given time interval. Each node represents a contributor (🔴 Core 🔵 Peripheral). The edges represent the connections between contributors. The more cental a node is, the more a given contributor has contributed to the project.",
                                target="graph-tooltip",
                                placement="top-start",
                                style={"background-color": "white", "color": "#000", "max-width": "750px"}
                            ),
                        ]),
                        html.Div(
                            style={"margin-top": "20px"},
                            children=[
                                dcc.RangeSlider(
                                    id="graph-slider",
                                    min=0,
                                    max=5,
                                    value=[0, 1],
                                    marks={
                                        0: "1/2019",
                                        1: "4/2019",
                                        2: "7/2019",
                                        3: "10/2019",
                                        4: "1/2020",
                                        5: "4/2020"
                                    },
                                    step=1
                                ),
                                html.Button('▶', id='play-button', n_clicks=0, style={'margin-left': '10px', 'margin-right': '10px'}),
                                html.Button('⏸', id='pause-button', n_clicks=0),
                            ]
                        ),
                        dcc.Interval(id='animation-interval', interval=1000, disabled=True)  # Disabled by default
                    ]
                ),
            ]
        )

#------------------------------------------------------ CALLBACKS ------------------------------------------------------ 

# control animation based on play and pause button clicks 
@app.callback(
    Output('animation-interval', 'disabled'),
    Output('animation-interval', 'interval'),
    Input('play-button', 'n_clicks'),
    Input('pause-button', 'n_clicks'),
    State('animation-interval', 'disabled'),
    State('graph-slider', 'value'),
    prevent_initial_call=True
)
def toggle_animation(play_clicks, pause_clicks, interval_disabled, slider_value):
    if play_clicks > pause_clicks:
        return False, 5000  # Enable the interval and set the interval duration (in milliseconds)
    else:
        return True, None  # Disable the interval


@app.callback(
    Output('graph-slider', 'value'),
    Input('animation-interval', 'n_intervals'),
    State('graph-slider', 'value'),
    State('graph-slider', 'max'),
    prevent_initial_call=True
)
def update_slider_value(n_intervals, slider_value, slider_max):
    # Increment the slider value by one until it reaches the maximum, then reset it to the minimum
    new_value = [(slider_value[0] + 1) % (slider_max + 1), (slider_value[1] + 1) % (slider_max + 1)]
    return new_value

# display the network graph
@app.callback(
    Output('graph-animation', 'figure'),
    Input('submit-button', 'n_clicks'),
    Input('animation-interval', 'n_intervals'),
    State('repo-org', 'value'),
    State('repo-name', 'value'),
    State('graph-slider', 'value'),
    State('graph-slider', 'marks'),
    State('cmt-weight', 'value'), 
    State('ism-weight', 'value'), 
    State('pr-weight', 'value'), 
    State('prm-weight', 'value'),
    State('threshold-dropdown', 'value'), 
    State('number-input', 'value'),
    prevent_initial_call=True
)
def update_network(n_clicks, n_intervals, repo_org, repo_name, slider_value, slider_marks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold_type, threshold_value):
    data = fetch_data(repo_org, repo_name, ['cmt', 'ism', 'pr', 'prm'])
    start_month, start_year = map(int, slider_marks[str(slider_value[0])].split("/"))
    end_month, end_year = map(int, slider_marks[str(slider_value[1])].split("/"))
    G = build_graph(data, start_month, start_year, end_month, end_year, cmt_weight, ism_weight, pr_weight, prm_weight)
    pagerank_scores, scaled_scores = pagerank(G)
    threshold_score = find_threshold(np.array(list(pagerank_scores.values())), [threshold_type, threshold_value])

    return draw_network(G, slider_value, slider_marks, pagerank_scores, scaled_scores, threshold_score)