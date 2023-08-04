import numpy as np
import pandas as pd 
import networkx as nx
import plotly.graph_objs as go
from graph_utils.graph_helper import find_threshold, build_graph
import datetime as dt


def get_plot_data(data, marks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold): 
    """
    Get plot data for each interval frame of the network graph. The data collected at each interval includes: 
        - core: count of core nodes
        - peripheral: count of peripheral nodes
        - new: count of net new nodes (not previously seen in the network)
        - all_time: net count of all nodes over current and prior intervals
        - promo: count of core nodes that were peripheral in the previous interval
        - demo: count of peripheral nodes that were core in the previous interval 
        - avg_intervals: average number of intervals current core nodes have spent as core

    Args:
    -----
        data (tuple): A tuple containing four data frames (cmt_data, ism_data, pr_data, prm_data).
        marks (list): A list of date marks representing intervals for the network graph.
        cmt_weight, ism_weight, pr_weight, prm_weight (float): The weights to assign to edges in 
                                                               the graph based on event type.
        threshold (tuple): A tuple containing the threshold type and the corresponding value for 
                           threshold calculation. The tuple format should be 
                           (threshold_type, threshold_value).

    Returns:
    --------
        pd.DataFrame: A Pandas DataFrame containing the calculated metrics for each interval frame 
                      of the network graph.

    """

    #initialize dataframe to store plot data
    plot_df = pd.DataFrame(columns=['core', 'peripheral', 'new', 'all_time', 'promo', 'demo', 'avg_intervals'])

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

        # update core_nodes and peripheral_nodes based on the threshold condition
        core_nodes = set()
        peripheral_nodes = set()
        for node in set(G.nodes()):
            if pagerank_scores[node] >= threshold_score:
                core_nodes.add(node)
            else:
                peripheral_nodes.add(node)

        # calculate the net new nodes 
        new_nodes = set(G.nodes()) - prev_nodes

        # populate core intervals
        for node in core_nodes:
            core_intervals[node] = core_intervals.get(node, 0) + 1
        avg_interval = sum(core_intervals[node] for node in core_nodes) / len(core_nodes)

        prev_nodes = prev_nodes | set(G.nodes())
        peripheral_to_core = len(prev_peripheral.intersection(core_nodes)) # promotion
        core_to_peripheral = len(prev_core.intersection(peripheral_nodes)) # demotion

        # update the prev_core, and prev_peripheral variables for the next frame
        prev_core = core_nodes
        prev_peripheral = peripheral_nodes

        # append the data to the df for this frame
        plot_df.loc[frame] = {
            'core': len(core_nodes),
            'peripheral': len(peripheral_nodes),
            'new': len(new_nodes),
            'all_time': len(prev_nodes),
            'promo': peripheral_to_core,
            'demo': core_to_peripheral,
            'avg_intervals': avg_interval
        }

    return plot_df

def init_sets(G):
    """
    Initialize sets for the first frame of the network graph.

    Args:
    -----
        G (nx.Graph): The input graph representing interactions among contributors.

    Returns:
    --------
        tuple: A tuple containing four sets and a dictionary:
            - prev_nodes (set): A set containing all nodes in the graph for the first frame.
            - prev_peripheral (set): An empty set for the first frame (no peripheral nodes).
            - prev_core (set): An empty set for the first frame (no core nodes).
            - core_intervals (dict): An empty dictionary for counting intervals for core nodes.
    """

    prev_nodes = set(G.nodes())
    prev_peripheral = set()
    prev_core = set()
    core_intervals = {}

    return prev_nodes, prev_peripheral, prev_core, core_intervals

def add_trace(df_table, name, color, marks):
    """
    Create a Plotly Scatter trace with provided data for visualization.

    Args:
        df_table (pd.Series): The data points to be plotted on the y-axis.
        name (str): The name of the trace, which will be displayed in the legend.
        color (str or dict): The color of the line as a string representing a color name 
                             (e.g., 'red', 'blue', 'green').
        marks (list): The corresponding x-axis values (slider marks) for the data points.

    Returns:
        go.Scatter: A Plotly Scatter trace representing the line plot with the provided data.
    """

    trace = go.Scatter(
        y = df_table,
        x = marks,
        mode = 'lines',
        name = name,
        line = dict(shape = 'linear', color = color, width = 2),
        connectgaps = True
    )
    return trace
