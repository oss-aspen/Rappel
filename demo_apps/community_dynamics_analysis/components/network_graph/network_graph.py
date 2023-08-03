import plotly.graph_objs as go
import matplotlib.pyplot as plt
import networkx as nx

plt.switch_backend('Agg') 

def draw_network(G, start_date, end_date, pagerank_scores, norm_scores, threshold_score):
    """
    Draw and visualize a network graph based on nx.Graph object 
    data using a combination of NetworkX and Plotly libraries.

    Args:
    -----
        G (nx.Graph): The input graph representing interactions among contributors. Nodes in the 
                      graph represent contributors, and edges represent different types of 
                      interactions between contributors.
        start_date, end_date (datetime.date): The start and end date defining the time range for snapshot 
                                              data inclusion in the graph visualization.
        pagerank_scores (dict): A dictionary containing contributors as keys and their corresponding 
                                PageRank scores as values.
        norm_scores (dict): A dictionary containing contributors as keys and their scaled PageRank 
                              scores (normalized to the range [5,20] as values, used for node size 
                              determination in the visualization.
        threshold_score (float): A threshold value used to differentiate nodes based on their PageRank 
                                 scores. Core contributors with scores greater than or equal to this 
                                 threshold will be displayed in red, while those with lower scores 
                                 (peripheral) will be displayed in blue.

    Returns:
    --------
        go.Figure: A Plotly Figure object representing the network graph visualization.
    """

    fig = plt.subplots(figsize=(20, 20))
    node_colors = ['red' if pagerank_scores[n] >= threshold_score else 'blue' for n in G.nodes()]
    node_sizes = [norm_scores[node] for node in G.nodes()]
    pos = nx.spring_layout(G, iterations=50) #k=0.5,
    edge_trace, node_trace = draw_network_traces(G, pos, node_colors, node_sizes)
    start_date = start_date.strftime("%m/%Y")
    end_date = end_date.strftime("%m/%Y")
    fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title=(f"{start_date}-{end_date}"),
                    titlefont_size=20,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    figure = go.Figure(data=fig)

    return figure

def draw_network_traces(G, pos, node_colors, node_sizes):
    """
    Create edge and node traces for a network graph visualization.

    Args:
    -----------
        G (nx.Graph): The input graph representing interactions among contributors. Nodes in the graph 
                      represent contributors, and edges represent different types of interactions 
                      between contributors.
        pos (dict): A dictionary containing node positions as keys (contributors) and their respective 
                    positions in the visualization as values. 
        node_colors (list): A list of colors for nodes in the graph, where each color corresponds to a 
                            contributor based on certain criteria (e.g., core, peripheral, new).
        node_sizes (list): A list of sizes for nodes in the graph, where each size corresponds to a 
                            contributor based on their centrality calculated via Pagerank score.

    Returns:
    --------
        tuple: A tuple containing two Plotly Scatter objects representing the edge and node traces for 
               the network graph visualization.
    """
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
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_count = G.nodes[node]['count']
        contributions_text = '# of contributions: ' + str(node_count)
        adjacencies = G.adj[node]  # adjacent nodes for the current node
        connections_text = '# of connections: ' + str(len(adjacencies))
        node_text.append(contributions_text + '<br>' + connections_text)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        marker=dict(size = node_sizes, color = node_colors),
        text = node_text,
        mode='markers',
        hoverinfo='text')

    return edge_trace, node_trace
