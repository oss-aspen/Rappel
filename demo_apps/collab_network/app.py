import dash
import numpy as np
from dash import dcc, html, Dash, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import sqlalchemy as salc
import json
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from collections import Counter
import datetime
from plotly.subplots import make_subplots
import pickle
import scipy 

plt.switch_backend('Agg') 


with open("copy_cage-padres.json") as config_file:
    config = json.load(config_file)

# connect to Augur database
database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})

#------------------------------------------------------ AUGUR QUERY ------------------------------------------------------ 

def fetch_data(repo_org, repo_name):
  # commit author query
  cmt_query = salc.sql.text(f"""
                  SET SCHEMA 'augur_data';
                  SELECT
                      DISTINCT c.cmt_commit_hash,
                      c.cmt_committer_timestamp as timestamp,
                      (SELECT ca.cntrb_id FROM contributors_aliases ca WHERE c.cmt_author_email = ca.alias_email) as author_id,
                      (SELECT ca.cntrb_id FROM contributors_aliases ca WHERE c.cmt_committer_email = ca.alias_email) as committer_id
                  FROM
                      repo_groups rg,
                      repo r,
                      commits c
                  WHERE
                      c.repo_id = r.repo_id AND
                      rg.repo_group_id = r.repo_group_id AND
                      rg.rg_name = \'{repo_org}\' AND
                      r.repo_name = \'{repo_name}\' AND
                      c.cmt_author_email != c.cmt_committer_email
                  GROUP BY
                      c.cmt_commit_hash,
                      c.cmt_author_email,
                      c.cmt_committer_email,
                      c.cmt_committer_timestamp
                  ORDER BY
                      timestamp DESC
          """)

  cmt_data = pd.read_sql(cmt_query, con=engine)
  cmt_data = cmt_data.dropna()
  cmt_data['year'] = pd.to_datetime(cmt_data['timestamp'], utc=True).dt.year
  cmt_data['month'] = pd.to_datetime(cmt_data['timestamp'], utc=True).dt.month

  # issue message query
  ism_query = salc.sql.text(f"""
                 SET SCHEMA 'augur_data';
                 SELECT
                    i.issue_id,
                    m.cntrb_id,
                    i.closed_at as timestamp
                FROM
                    repo_groups rg,
                    repo r,
                    issues i,
                    issue_message_ref imr,
                    message m
                WHERE
                    rg.repo_group_id = r.repo_group_id AND
                    i.repo_id = r.repo_id AND
                    i.issue_id = imr.issue_id AND
                    m.msg_id = imr.msg_id AND
                    rg.rg_name = \'{repo_org}\' AND
                    r.repo_name = \'{repo_name}\'
                GROUP BY
                    i.issue_id,
                    m.cntrb_id,
                    timestamp
        """)

  ism_data = pd.read_sql(ism_query, con=engine)

  # reformat issue message data
  ism_data = ism_data.groupby('issue_id').agg({'cntrb_id': list, 'timestamp': 'last'}).reset_index()
  ism_data = ism_data[ism_data['cntrb_id'].apply(lambda x: len(x) > 1)]
  ism_data = ism_data.sort_values('timestamp', ascending=False)
  ism_data['year'] = pd.to_datetime(ism_data['timestamp'], utc=True).dt.year
  ism_data['month'] = pd.to_datetime(ism_data['timestamp'], utc=True).dt.month

  # pull request reviewer query
  pr_query = salc.sql.text(f"""
                  SET SCHEMA 'augur_data';
                  SELECT
                      pr.pull_request_id,
                      pre.cntrb_id,
                      prr.cntrb_id as reviewer,
                      pr.pr_created_at as timestamp
                  FROM
                      repo_groups rg,
                      repo r,
                      pull_requests pr,
                      pull_request_events pre,
                      pull_request_reviewers prr
                  WHERE
                      rg.repo_group_id = r.repo_group_id AND
                      pr.repo_id = r.repo_id AND
                      pr.pull_request_id = pre.pull_request_id AND
                      pr.pull_request_id = prr.pull_request_id AND
                      pre.cntrb_id != prr.cntrb_id AND
                      rg.rg_name = \'{repo_org}\' AND
                      r.repo_name = \'{repo_name}\'
                  GROUP BY
                      pr.pull_request_id,
                      pre.cntrb_id,
                      prr.cntrb_id,
                      timestamp
                  ORDER BY
                      timestamp DESC
          """)

  pr_data = pd.read_sql(pr_query, con=engine)
  pr_data = pr_data.dropna()
  pr_data['year'] = pd.to_datetime(pr_data['timestamp'], utc=True).dt.year
  pr_data['month'] = pd.to_datetime(pr_data['timestamp'], utc=True).dt.month

  # pull request message query
  prm_query = salc.sql.text(f"""
                  SET SCHEMA 'augur_data';
                  SELECT
                      pr.pull_request_id,
                      m.cntrb_id,
                      pr.pr_created_at as timestamp
                  FROM
                      repo_groups rg,
                      repo r,
                      pull_requests pr,
                      pull_request_message_ref prm,
                      message m
                  WHERE
                      rg.repo_group_id = r.repo_group_id AND
                      pr.repo_id = r.repo_id AND
                      pr.pull_request_id = prm.pull_request_id AND
                      m.msg_id = prm.msg_id AND
                      rg.rg_name = \'{repo_org}\' AND
                      r.repo_name = \'{repo_name}\'
                  GROUP BY
                      pr.pull_request_id,
                      m.cntrb_id,
                      timestamp
          """)

  prm_data = pd.read_sql(prm_query, con=engine)

  # reformat pull request message data
  prm_data = prm_data.groupby('pull_request_id').agg({'cntrb_id': list, 'timestamp': 'last'}).reset_index()
  prm_data = prm_data[prm_data['cntrb_id'].apply(lambda x: len(x) > 1)]
  prm_data = prm_data.sort_values('timestamp', ascending=False)
  prm_data['year'] = pd.to_datetime(prm_data['timestamp'], utc=True).dt.year
  prm_data['month'] = pd.to_datetime(prm_data['timestamp'], utc=True).dt.month

  return cmt_data, ism_data, pr_data, prm_data

#------------------------------------------------------ INTERVAL CALCULATION ------------------------------------------------------ 

def get_intervals(start_year, start_month, end_year, end_month, interval): 
    total_frames = ((end_year - start_year) * 12 + (end_month - start_month)) // interval
    # generate intervals
    intervals = []
    for frame in range(total_frames):
        snap_end_month = start_month + interval - 1
        snap_end_year = start_year
        if snap_end_month > 12:
            snap_end_month -= 12
            snap_end_year += 1

        intervals.append(f"{start_month}/{start_year}-{snap_end_month}/{snap_end_year}")

        start_year = snap_end_year
        start_month = snap_end_month + 1
        if start_month > 12:
            start_month = 1
            start_year += 1

    return intervals

def get_marks(start_year, start_month, end_year, end_month, interval):
    total_frames = ((end_year - start_year) * 12 + (end_month - start_month)) // interval + 1
    marks = []
    for frame in range(total_frames):
        snap_end_month = start_month + interval -1
        snap_end_year = start_year
        if snap_end_month > 12:
            snap_end_month -= 12
            snap_end_year += 1

        marks.append(f"{start_month}/{start_year}") 

        start_year = snap_end_year
        start_month = snap_end_month + 1
        if start_month > 12:
            start_month = 1
            start_year += 1
    return marks 

#------------------------------------------------------ GET DATA FOR PLOTS ------------------------------------------------------ 
# threshold not implemented 
def get_plot_data(repo_org, repo_name, start_year, start_month, end_year, end_month, interval, cmt_weight, ism_weight, pr_weight, prm_weight): 
    cmt_data, ism_data, pr_data, prm_data = fetch_data(repo_org, repo_name)

    snapshot_G = nx.Graph()
    last_nodes = set()
    prev_nodes = set()
    prev_core = set()
    prev_peripheral = set()
    peripheral_to_core_list = []
    core_to_peripheral_list = []

    # initialize lists for plot
    core = []
    peripheral = []
    new = []
    core_intervals = {}
    avg_intervals = {}

    # calculate the total number of frames
    total_frames = ((end_year - start_year) * 12 + (end_month - start_month)) // interval
    last_frame_reached = False

    # define a function to update the graph for each frame of the animation
    def update_graph(frame):
        global snap_start_year, snap_start_month, last_nodes, prev_nodes, prev_core, prev_peripheral, core_intervals, last_frame_reached

        if frame == 0:
            snap_start_year = start_year
            snap_start_month = start_month

        snap_end_month = snap_start_month + interval - 1
        snap_end_year = snap_start_year
        if snap_end_month > 12:
            snap_end_month -= 12
            snap_end_year += 1

        # add nodes and edges to the snapshot_G graph based on the snapshot data
        snapshot_cmt = cmt_data[(cmt_data['year'].between(snap_start_year, snap_end_year)) &
                                (cmt_data['month'].between(snap_start_month, snap_end_month))].dropna()
        snapshot_pr = pr_data[(pr_data['year'].between(snap_start_year, snap_end_year)) &
                              (pr_data['month'].between(snap_start_month, snap_end_month))].dropna()
        snapshot_ism = ism_data[(ism_data['year'].between(snap_start_year, snap_end_year)) &
                                (ism_data['month'].between(snap_start_month, snap_end_month))].dropna()
        snapshot_prm = prm_data[(prm_data['year'].between(snap_start_year, snap_end_year)) &
                                (prm_data['month'].between(snap_start_month, snap_end_month))].dropna()

        # cmt_data
        edge_counts = snapshot_cmt.groupby(['author_id', 'committer_id']).size()
        for (author, committer), weight in edge_counts.items():
            if author != committer:
                if not snapshot_G.has_node(author):
                    snapshot_G.add_node(author)
                if not snapshot_G.has_node(committer):
                    snapshot_G.add_node(committer)
                if snapshot_G.has_edge(author, committer):
                    snapshot_G[author][committer]['weight'] += cmt_weight
                else:
                    snapshot_G.add_edge(author, committer, weight=cmt_weight)

        # ism_data
        for row in snapshot_ism.itertuples():
            issue_id = row.issue_id
            contributors = row.cntrb_id
            for cntrb in contributors:
                if not snapshot_G.has_node(cntrb):
                    snapshot_G.add_node(cntrb)
            for i in range(len(contributors)):
                for j in range(i+1, len(contributors)):
                    if contributors[i] != contributors[j]:
                        if snapshot_G.has_edge(contributors[i], contributors[j]):
                            snapshot_G[contributors[i]][contributors[j]]['weight'] += ism_weight
                        else:
                            snapshot_G.add_edge(contributors[i], contributors[j], issue=issue_id, weight=ism_weight)

        # pr_data
        for _, row in snapshot_pr.iterrows():
            if row['cntrb_id'] != row['reviewer']:
                if not snapshot_G.has_node(row['cntrb_id']):
                    snapshot_G.add_node(row['cntrb_id'])
                if not snapshot_G.has_node(row['reviewer']):
                    snapshot_G.add_node(row['reviewer'])
                if snapshot_G.has_edge(row['cntrb_id'], row['reviewer']):
                    snapshot_G[row['cntrb_id']][row['reviewer']]['weight'] += pr_weight
                else:
                    snapshot_G.add_edge(row['cntrb_id'], row['reviewer'], weight=pr_weight)

        # prm_data
        for row in snapshot_prm.itertuples():
            pr_id = row.pull_request_id
            contributors = row.cntrb_id
            for cntrb in contributors:
                if not snapshot_G.has_node(cntrb):
                    snapshot_G.add_node(cntrb)
            for i in range(len(contributors)):
                for j in range(i+1, len(contributors)):
                    if contributors[i] != contributors[j]:
                        if snapshot_G.has_edge(contributors[i], contributors[j]):
                            snapshot_G[contributors[i]][contributors[j]]['weight'] += prm_weight
                        else:
                            snapshot_G.add_edge(contributors[i], contributors[j], pr=pr_id, weight=prm_weight)

        # calculate pagerank score threshold
        pagerank_scores = nx.pagerank(snapshot_G)

        #threshold_score = find_threshold(np.array(list(pagerank_scores.values())), threshold)
        scores = np.sort(np.array(list(pagerank_scores.values())))
        diff = np.diff(scores)
        knee_index = np.argmax(diff) + 1
        threshold_score = scores[knee_index]
    
        if frame == 0:
            prev_nodes = set(snapshot_G.nodes())
            last_nodes = set(snapshot_G.nodes())
            prev_peripheral = set()
            prev_core = set()
            core_intervals = {}

        node_colors = ['r' if pagerank_scores[n] >= threshold_score else 'b' if n in prev_nodes else 'y' for n in snapshot_G.nodes()]
        core_nodes = set([node for node in set(snapshot_G.nodes()) if pagerank_scores[node] >= threshold_score])
        peripheral_nodes = set([node for node in set(snapshot_G.nodes()) if pagerank_scores[node] < threshold_score])

        # populate core intervals
        for node in core_nodes:
            core_intervals[node] = core_intervals.get(node, 0) + 1

        avg_intervals[frame] = sum(core_intervals[node] for node in core_nodes) / len(core_nodes)

        prev_nodes = prev_nodes | set(snapshot_G.nodes())
        peripheral_to_core = len(prev_peripheral.intersection(core_nodes))
        core_to_peripheral = len(prev_core.intersection(peripheral_nodes))

        # update the prev_nodes, prev_core, and prev_peripheral variables for the next frame
        last_nodes = set(snapshot_G.nodes())
        prev_core = core_nodes
        prev_peripheral = peripheral_nodes
        
        counts = Counter(node_colors)
        core.append(counts['r'])
        peripheral.append(counts['b'])
        new.append(counts['y'])
        peripheral_to_core_list.append(peripheral_to_core)
        core_to_peripheral_list.append(core_to_peripheral)

        snap_start_year = snap_end_year
        snap_start_month = snap_end_month + 1

        if snap_start_month > 12:
            snap_start_month = 1
            snap_start_year += 1

        if frame == total_frames - 1:
            last_frame_reached = True
            return None

        return core, peripheral, new, peripheral_to_core_list, core_to_peripheral_list, avg_intervals
    
    for frame in range(total_frames): 
        update_graph(frame)

    return core, peripheral, new, peripheral_to_core_list, core_to_peripheral_list, avg_intervals

#------------------------------------------------------ PLOT TRENDS ------------------------------------------------------ 
def draw_plots(intervals, core, peripheral, new, peripheral_to_core_list, core_to_peripheral_list, avg_intervals):
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
    return core_trace, per_trace, new_trace, promo_trace, demo_trace, avg_int_trace

#------------------------------------------------------ NETWORK GRAPH ------------------------------------------------------ 
def draw_network(slider_value, slider_marks, data, cmt_weight, ism_weight, pr_weight, prm_weight): 
    cmt_data, ism_data, pr_data, prm_data = data
    start_month, start_year = map(int, slider_marks[str(slider_value[0])].split("/"))
    end_month, end_year = map(int, slider_marks[str(slider_value[1])].split("/"))

    snapshot_cmt = cmt_data[(cmt_data['year'].between(start_year, end_year)) &
                                (cmt_data['month'].between(start_month, end_month))].dropna()
    snapshot_pr = pr_data[(pr_data['year'].between(start_year, end_year)) &
                              (pr_data['month'].between(start_month, end_month))].dropna()
    snapshot_ism = ism_data[(ism_data['year'].between(start_year, end_year)) &
                                (ism_data['month'].between(start_month, end_month))].dropna()
    snapshot_prm = prm_data[(prm_data['year'].between(start_year, end_year)) &
                                (prm_data['month'].between(start_month, end_month))].dropna()
    
    fig, ax = plt.subplots(figsize=(20, 20))
    G = nx.Graph()

    # cmt_data
    edge_counts = snapshot_cmt.groupby(['author_id', 'committer_id']).size()
    for (author, committer), weight in edge_counts.items():
            if author != committer:
                if not G.has_node(author):
                    G.add_node(author)
                if not G.has_node(committer):
                    G.add_node(committer)
                if G.has_edge(author, committer):
                    G[author][committer]['weight'] += cmt_weight
                else:
                    G.add_edge(author, committer, weight=cmt_weight)

    # ism_data
    for row in snapshot_ism.itertuples():
            issue_id = row.issue_id
            contributors = row.cntrb_id
            for cntrb in contributors:
                if not G.has_node(cntrb):
                    G.add_node(cntrb)
            for i in range(len(contributors)):
                for j in range(i+1, len(contributors)):
                    if contributors[i] != contributors[j]:
                        if G.has_edge(contributors[i], contributors[j]):
                            G[contributors[i]][contributors[j]]['weight'] += ism_weight
                        else:
                            G.add_edge(contributors[i], contributors[j], issue=issue_id, weight=ism_weight)

    # pr_data
    for _, row in snapshot_pr.iterrows():
            if row['cntrb_id'] != row['reviewer']:
                if not G.has_node(row['cntrb_id']):
                    G.add_node(row['cntrb_id'])
                if not G.has_node(row['reviewer']):
                    G.add_node(row['reviewer'])
                if G.has_edge(row['cntrb_id'], row['reviewer']):
                    G[row['cntrb_id']][row['reviewer']]['weight'] += pr_weight
                else:
                    G.add_edge(row['cntrb_id'], row['reviewer'], weight=pr_weight)

    # prm_data
    for row in snapshot_prm.itertuples():
            pr_id = row.pull_request_id
            contributors = row.cntrb_id
            for cntrb in contributors:
                if not G.has_node(cntrb):
                    G.add_node(cntrb)
            for i in range(len(contributors)):
                for j in range(i+1, len(contributors)):
                    if contributors[i] != contributors[j]:
                        if G.has_edge(contributors[i], contributors[j]):
                            G[contributors[i]][contributors[j]]['weight'] += prm_weight
                        else:
                            G.add_edge(contributors[i], contributors[j], pr=pr_id, weight=prm_weight)

        # calculate pagerank scores and scale to use for node sizes
    pagerank_scores = nx.pagerank(G)
    min_score = min(pagerank_scores.values())
    max_score = max(pagerank_scores.values())
    min_size = 50
    max_size = 150
    scaled_scores = {node: (pagerank_scores[node] - min_score) / (max_score - min_score) for node in G.nodes()}

    # calculate elbow score to use for threshold
    #threshold_score = find_threshold(np.array(list(pagerank_scores.values())), threshold)
    scores = np.sort(np.array(list(pagerank_scores.values())))
    diff = np.diff(scores)
    knee_index = np.argmax(diff) + 1
    threshold_score = scores[knee_index]

    node_colors = ['red' if pagerank_scores[n] >= threshold_score else 'blue' for n in G.nodes()]
    node_sizes = [min_size + (max_size - min_size) * scaled_scores[node] for node in G.nodes()]
    edge_widths = [G[u][v]['weight'] * 0.1 for u, v in G.edges()]
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, ax=ax)
    nx.draw_networkx_edges(G, pos, width=edge_widths, ax=ax)
    ax.set_title(f"{start_month}/{start_year}-{end_month}/{end_year}", fontsize=30)

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
    
    fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title=(f"{slider_marks[str(slider_value[0])]}-{slider_marks[str(slider_value[1])]}"),
                    titlefont_size=20,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )

    return [go.Figure(data=fig)]


#------------------------------------------------------ APP ------------------------------------------------------ 

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
        html.Div(
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
                                #html.Div(html.Button("Show", id="resubmit-button", n_clicks=0))
                            ]
                        )
                    ]
                ),
            ]
        ),
        html.Div(
            className="column",
            style={"flex": "33%"},
            children=[
                html.Div(
                    className="graph-container",
                    children=[
                        dcc.Graph(id="contributor-type-cardinality"),
                        dcc.Checklist(
                            id="cardinality-checklist",
                            options=["core", "peripheral", "new"],
                            value=["core", "peripheral", "new"],
                            inline=True,
                            style = {"padding-left": "30px"}
                        )
                    ]
                ),
                html.Div(
                    className="graph-container",
                    children=[
                        dcc.Graph(id="promotions-demotions"),
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
                        dcc.Graph(id="average-intervals")
                    ]
                )
            ]
        ), html.Div(
            className="sidebar",
            style={
                "flex": "17%",
                "background-color": "#f8f9fa",
                "padding": "20px",
                "border-radius": "5px",
                "box-shadow": "0px 2px 6px rgba(0, 0, 0, 0.1)"
            },
            children=[
                html.H2("Parameters", style={"margin-bottom": "20px"}),
                html.Label("Repository:  "),
                html.Br(),
                dcc.Input(id="repo-org", type="text", placeholder="Repo Org", style={"margin-bottom": "10px"}),
                dcc.Input(id="repo-name", type="text", placeholder="Repo Name", style={"margin-bottom": "10px"}),
                html.Br(),
                html.Label("Start Date:  "),
                html.Br(),
                dcc.Input(id="start-year", type="number", placeholder="Year", style={"margin-bottom": "10px"}),
                dcc.Input(id="start-month", type="number", placeholder="Month", style={"margin-bottom": "10px"}),
                html.Br(),
                html.Label("End Date:  "),
                html.Br(),
                dcc.Input(id="end-year", type="number", placeholder="Year", style={"margin-bottom": "10px"}),
                dcc.Input(id="end-month", type="number", placeholder="Month", style={"margin-bottom": "10px"}),
                html.Br(),
                html.Label("Time Interval:  "),
                html.Br(),
                dcc.Input(id="interval", type="number", placeholder="Months", style={"margin-bottom": "10px"}),
                html.Br(),
                html.Br(),
                html.H4("Threshold Calculation:"),
                dcc.Dropdown(
                    id="threshold-dropdown",
                    options=[
                        {"label": "Elbow", "value": "elbow"},
                        {"label": "Percentage top contributors", "value": "percentage"},
                        {"label": "Number top contributors", "value": "number"}
                    ],
                    value="elbow",
                    style={"width": "100%", "margin-bottom": "10px"}
                ),
                html.P(
                    "Optional: default = elbow",
                    style={"font-size": "12px", "color": "gray"}
                ),
                html.Div(id="threshold-input"),
                html.Br(),
                html.H4("Event Type Weights:"),
                html.Label("Commit author:"),
                dcc.Slider(id="cmt-weight", min=0, max=2, step=0.1, value=1.0, marks={i: str(i) for i in [0, 0.5, 1, 1.5, 2]}),
                html.Br(),
                html.Label("Issue message thread:"),
                dcc.Slider(id="ism-weight", min=0, max=2, step=0.1, value=0.1, marks={i: str(i) for i in [0, 0.5, 1, 1.5, 2]}),
                html.Br(),
                html.Label("PR reviewer:"),
                dcc.Slider(id="pr-weight", min=0, max=2, step=0.1, value=2.0, marks={i: str(i) for i in [0, 0.5, 1, 1.5, 2]}),
                html.Br(),
                html.Label("PR message thread:"),
                dcc.Slider(id="prm-weight", min=0, max=2, step=0.1, value=0.5, marks={i: str(i) for i in [0, 0.5, 1, 1.5, 2]}),
                html.P(
                    "Optional: default = 1.0, 0.1, 2.0, 0.5 (based on Orbit model)",
                    style={"font-size": "12px", "color": "gray"}
                ),
                html.Br(),
                html.Br(),
                html.Div(html.Button("Submit", id="submit-button", n_clicks=0))
            ]
        )
        
    ]
)

# update slider
@app.callback(
    [
        Output('graph-slider', 'max'),
        Output('graph-slider', 'marks'),
        Input('submit-button', 'n_clicks'), 
        State('start-year', 'value'),
        State('start-month', 'value'),
        State('end-year', 'value'),
        State('end-month', 'value'),
        State('interval', 'value')
    ],
    prevent_initial_call=True
)
def set_slider(n_clicks, start_year, start_month, end_year, end_month, interval): 
    intervals = get_marks(start_year, start_month, end_year, end_month, interval)
    marks = {}
    for i, interval_str in enumerate(intervals):
        marks[i] = interval_str
    return len(intervals)-1, marks



# generate graphs
@app.callback(
    [
        Output('graph-animation', 'figure')
    ],
    [
        Input('submit-button', 'n_clicks')
    ],
    [
        State('repo-org', 'value'),
        State('repo-name', 'value'),
        State('graph-slider', 'value'),
        State('graph-slider', 'marks')
    ],
    prevent_initial_call=True
)
def update_network(n_clicks, repo_org, repo_name, slider_value, slider_marks):
    data = fetch_data(repo_org, repo_name)
    return draw_network(slider_value, slider_marks, data)

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
        State('prm-weight', 'value')
    ],
    prevent_initial_call=True
)
def plot(n_clicks, repo_org, repo_name, start_year, start_month, end_year, end_month, interval, card_checks, promo_checks, cmt_weight, ism_weight, pr_weight, prm_weight):

    intervals = get_intervals(start_year, start_month, end_year, end_month, interval)
    core, peripheral, new, peripheral_to_core_list, core_to_peripheral_list, avg_intervals = get_plot_data(repo_org, repo_name, start_year, start_month, end_year, end_month, interval, cmt_weight, ism_weight, pr_weight, prm_weight)
    core_trace, per_trace, new_trace, promo_trace, demo_trace, avg_int_trace = draw_plots(intervals, core, peripheral, new, peripheral_to_core_list, core_to_peripheral_list, avg_intervals)
     
    data1 = []
    for c in card_checks: 
        if c == "core":
            data1.append(core_trace)
        if c == "peripheral": 
            data1.append(per_trace)
        if c == "new":
            data1.append(new_trace)

    data2 = []
    for c in promo_checks: 
        if c == "promotions":
            data2.append(promo_trace)
        if c == "demotions":
            data2.append(demo_trace)

    data3 = avg_int_trace
            
    layout1 =  dict(
        title = 'Cardinality by Contributor Type',
        yaxis = dict(title = 'Contributor Count'),
        xaxis = dict(title = 'Intervals')    
    )
    layout2 =  dict(
        title = 'Contributor Promotions and Demotions',
        yaxis = dict(title = 'Contributor Count'),
        xaxis = dict(title = 'Intervals')    
    )
    layout3 =  dict(
        title = ' Average intervals served as core',
        yaxis = dict(title = 'Average #intervals as core'),
        xaxis = dict(title = 'Intervals')    
    )

    fig1 =  go.Figure(data = data1, layout=layout1)
    fig2 =  go.Figure(data = data2, layout=layout2)
    fig3 =  go.Figure(data = data3, layout=layout3)

    return fig1, fig2, fig3
    
@app.callback(
    Output('threshold-input', 'children'),
    [Input('threshold-dropdown', 'value')],
    prevent_initial_call=True
)
def update_threshold_input(value):
    if value == 'elbow':
        return None
    elif value == 'percentage':
        return html.Div([
            html.Label("Percentage:"),
            dcc.Input(id='percentage-input', type='number', placeholder='Percentage')
        ])
    elif value == 'number':
        return html.Div([
            html.Label("Number:"),
            dcc.Input(id='number-input', type='number', placeholder='Number')
        ])

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
