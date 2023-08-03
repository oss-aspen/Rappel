import numpy as np
import networkx as nx


#------------------------------------------------------ THRESHOLD CALCULATION ------------------------------------------------------ 

def find_threshold(scores, threshold):
    """
    Takes in an array of scores and a threshold specification, and calculates
    the core node threshold score based on the given threshold type and value. The three 
    supported threshold types are:

    1. 'elbow': The threshold score will be the point of maximum curvature on the sorted 
       scores, which is determined by finding the index with the highest difference between 
       consecutive scores.

    2. 'percentage': The threshold score will be the value corresponding to a percentage of 
       the total scores length. The threshold value should be provided as a floating-point 
       number between 0 and 100, indicating the percentage of scores to be included in the 
       core nodes.

    3. 'number': The threshold score will be the value corresponding to a specific number 
       of top scores to be included in the core nodes. The threshold value should be an 
       integer indicating the number of top scores to be considered.

    Args:
    -----
        scores (array): An array of numeric values representing the pagerank scores 
                        of all nodes in the graph.
        threshold (tuple): A tuple containing the threshold type and the corresponding 
                           value for threshold calculation. The tuple format should be 
                           (threshold_type, threshold_value). 

    Returns:
    --------
        float: The core node threshold score calculated based on the specified 
               threshold type and value.
    """

    scores = np.sort(scores)

    if threshold[0] == 'elbow':  
        # calculate differencs between consecutive scores 
        diff = np.diff(scores) 
        # find the index where the difference between consecutive scores is highest
        elbow_index = np.argmax(diff) + 1
        threshold_score = scores[elbow_index] 
    elif threshold[0] == 'percentage':
        # calculate number of core nodes based on percentage
        subset_length = int(len(scores) * threshold[1] / 100.0)
        # negative index to get threshold score
        threshold_score = scores[-subset_length]
    elif threshold[0] == 'number':  
        # negative index to get threshold score
        threshold_score = scores[-threshold[1]]

    return threshold_score

#------------------------------------------------------ PAGERANK SCORES ------------------------------------------------------ 

def apply_pagerank(G): 
    """
    Calculate the PageRank scores and normalize them for node sizes.

    Args:
    -----
        G (NetworkX Graph): The input graph for which PageRank scores need to be calculated.

    Returns:
    --------
        tuple: A tuple containing two dictionaries:
            - pagerank_scores (dict): A dictionary with nodes as keys and their corresponding 
              PageRank scores as values.
            - norm_scores (dict): A dictionary with nodes as keys and their normalized PageRank 
              scores as values.
    """

    pagerank_scores = nx.pagerank(G)
    min_score = min(pagerank_scores.values())
    max_score = max(pagerank_scores.values())
    # normalize between 5 to 20 for plotting
    norm_scores = {node: (pagerank_scores[node] - min_score) / (max_score - min_score) * (20 - 5) + 5 for node in G.nodes()}
    
    return pagerank_scores, norm_scores

#------------------------------------------------------ BUILD GRAPH OBJECT ------------------------------------------------------ 

def build_graph(data, start_date, end_date, cmt_weight, ism_weight, pr_weight, prm_weight):
    """
    Build a weighted graph from snapshot data.

    The interactions captured in the snapshot data are:
    - Code commits (cmt_data) with corresponding author and committer IDs.
    - Issue message relationships (ism_data) with multiple contributors associated with messages on an issue.
    - Pull request review relationships (pr_data) with contributors and reviewers.
    - Pull request message relationships (prm_data) with contributors associated with pull request comments.

    The constructed graph contains nodes representing contributors and edges representing the 
    interactions between contributors. The weights of the edges represent the strength or 
    significance of each interaction type, which can be customized using the input weights.

    Args:
    -----
        data (tuple): A tuple containing four data frames (cmt_data, ism_data, pr_data, prm_data).
        start_date, end_date (datetime.date): The start and end date to define the time range
                                              for snapshot data inclusion in the graph.
        cmt_weight, ism_weight, pr_weight, prm_weight (float): The weights to assign to edges in 
                                                               the graph based on event type.

    Returns:
    --------
        nx.Graph: The constructed weighted graph (G) representing the interactions among contributors 
                  in the specified time range.
    """

    cmt_data, ism_data, pr_data, prm_data = data
    G = nx.Graph()

    # add commit interactions to graph
    G = add_cmt_data(G, cmt_data, start_date, end_date, cmt_weight)
    # add issue message interactions to graph
    G = add_ism_data(G, ism_data, start_date, end_date, ism_weight)
    # add pull request review interactions to graph
    G = add_pr_data(G, pr_data, start_date, end_date, pr_weight)
    # add pull request message interactions to graph
    G = add_prm_data(G, prm_data, start_date, end_date, prm_weight)
    
    return G


def add_cmt_data(G, data, start_date, end_date, weight):
    """
    Add commit interactions to the NetworkX graph for the specified time interval.

    Args:
    -----
        G (nx.Graph): The input graph representing interactions among contributors.
        data (pd.DataFrame): A DataFrame containing commit data with columns: 'author_id', 
                             'committer_id', and 'timestamp'.
        start_date, end_date (datetime.date): The start and end date defining the time range 
                                              for snapshot data inclusion in the graph.
        weight (float): The weight to assign to commit interactions.

    Returns:
    --------
        nx.Graph: The graph (G) updated with commit interactions for the specified time interval.
    """

    # get commit data for current interval
    snapshot = data[(data['timestamp'] >= start_date) & (data['timestamp'] <= end_date)]
  
    edge_counts = snapshot.groupby(['author_id', 'committer_id']).size()
    for (author, committer), weight in edge_counts.items():
        if author != committer:
            if not G.has_node(author):
                G.add_node(author, count=1)  
            else:
                G.nodes[author]['count'] += 1  # increase count 
            if not G.has_node(committer):
                G.add_node(committer, count=1)  
            else:
                G.nodes[committer]['count'] += 1  # increase count 
            if G.has_edge(author, committer): # if edge present, increase weight
                G[author][committer]['weight'] += weight
            else: # if not present, create edge and set weight
                G.add_edge(author, committer, weight=weight)
    return G


def add_ism_data(G, data, start_date, end_date, weight):
    """
    Add issue message interactions to the NetworkX graph for the specified time interval.

    Args:
    -----
        G (nx.Graph): The input graph representing interactions among contributors.
        data (pd.DataFrame): A DataFrame containing issue message data with columns: 'issue_id', 
                             'cntrb_id', and 'timestamp'.
        start_date, end_date (datetime.date): The start and end date defining the time range 
                                              for snapshot data inclusion in the graph.
        weight (float): The weight to assign to issue message interactions.

    Returns:
    --------
        nx.Graph: The graph (G) updated with issue message interactions for the specified time interval.
    """

    # get issue message data for current interval
    snapshot = data[(data['timestamp'] >= start_date) & (data['timestamp'] <= end_date)]

    for row in snapshot.itertuples():
        issue_id = row.issue_id
        contributors = row.cntrb_id
        for cntrb in contributors:
            if not G.has_node(cntrb):
                G.add_node(cntrb, count=1)  
            else:
                G.nodes[cntrb]['count'] += 1  # increase count 
        for i in range(len(contributors)):
            for j in range(i+1, len(contributors)):
                if contributors[i] != contributors[j]:
                    if G.has_edge(contributors[i], contributors[j]): # if edge present, increase weight
                        G[contributors[i]][contributors[j]]['weight'] += weight
                    else: # if not present, create edge and set weight
                        G.add_edge(contributors[i], contributors[j], issue=issue_id, weight=weight)
    return G

def add_pr_data(G, data, start_date, end_date, weight):
    """
    Add pull request review interactions to the NetworkX graph for the specified time interval.

    Args:
    -----
        G (nx.Graph): The input graph representing interactions among contributors.
        data (pd.DataFrame): A DataFrame containing pull request review data with columns: 
                             'cntrb_id', 'reviewer', and 'timestamp'.
        start_date, end_date (datetime.date): The start and end date defining the time range 
                                              for snapshot data inclusion in the graph.
        weight (float): The weight to assign to pull request review interactions.

    Returns:
    --------
        nx.Graph: The graph (G) updated with pull request review interactions for the specified time interval.
    """

    # get pull request review data for current interval
    snapshot = data[(data['timestamp'] >= start_date) & (data['timestamp'] <= end_date)]
    
    for _, row in snapshot.iterrows():
        if row['cntrb_id'] != row['reviewer']:
            if not G.has_node(row['cntrb_id']):
                G.add_node(row['cntrb_id'], count=1)  
            else:
                G.nodes[row['cntrb_id']]['count'] += 1  # increase count 
            if not G.has_node(row['reviewer']):
                G.add_node(row['reviewer'], count=1)  
            else:
                G.nodes[row['reviewer']]['count'] += 1  # increase count 
            if G.has_edge(row['cntrb_id'], row['reviewer']): # if edge present, increase weight
                G[row['cntrb_id']][row['reviewer']]['weight'] += weight
            else: # if not present, create edge and set weight
                G.add_edge(row['cntrb_id'], row['reviewer'], weight=weight)
    return G

def add_prm_data(G, data, start_date, end_date, weight): 
    """
    Add pull request message interactions to the NetworkX graph for the specified time interval.

    Args:
    -----
        G (nx.Graph): The input graph representing interactions among contributors.
        data (pd.DataFrame): A DataFrame containing pull request message data with columns: 
                             'pull_request_id', 'cntrb_id', and 'timestamp'.
        start_date, end_date (datetime.date): The start and end date defining the time range 
                                              for snapshot data inclusion in the graph.
        weight (float): The weight to assign to pull request message interactions.

    Returns:
    --------
        nx.Graph: The graph (G) updated with pull request message interactions for the specified time interval.
    """

    # get pull request message data for current interval
    snapshot = data[(data['timestamp'] >= start_date) & (data['timestamp'] <= end_date)]

    for row in snapshot.itertuples():
        pr_id = row.pull_request_id
        contributors = row.cntrb_id
        for cntrb in contributors:
            if not G.has_node(cntrb):
                G.add_node(cntrb, count=1)  
            else:
                G.nodes[cntrb]['count'] += 1  # increase count 
        for i in range(len(contributors)):
            for j in range(i+1, len(contributors)):
                if contributors[i] != contributors[j]:
                    if G.has_edge(contributors[i], contributors[j]): # if edge present, increase weight
                        G[contributors[i]][contributors[j]]['weight'] += weight 
                    else: # if not present, create edge and set weight
                        G.add_edge(contributors[i], contributors[j], pr=pr_id, weight=weight)
    return G