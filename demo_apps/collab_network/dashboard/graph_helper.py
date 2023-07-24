import numpy as np
import networkx as nx


#------------------------------------------------------ THRESHOLD CALCULATION ------------------------------------------------------ 

def find_threshold(scores, threshold):
    # calculate the core node threshold score given threshold type and value 
    scores = np.sort(scores)

    if threshold[0] == 'elbow':  
        diff = np.diff(scores)
        knee_index = np.argmax(diff) + 1
        threshold_score = scores[knee_index]
    elif threshold[0] == 'percentage':
        subset_length = int(len(scores) * threshold[1] / 100.0)
        threshold_score = scores[-subset_length]
    elif threshold[0] == 'number':  
        sorted_scores = np.partition(scores, -threshold[1])
        threshold_score = sorted_scores[-threshold[1]]

    return threshold_score

#------------------------------------------------------ PAGERANK SCORES ------------------------------------------------------ 

def pagerank(G): 
    # calculate pagerank scores and scale to use for node sizes
    pagerank_scores = nx.pagerank(G)
    min_score = min(pagerank_scores.values())
    max_score = max(pagerank_scores.values())
    scaled_scores = {node: (pagerank_scores[node] - min_score) / (max_score - min_score) for node in G.nodes()}
    
    return pagerank_scores, scaled_scores

#------------------------------------------------------ BUILD GRAPH OBJECT ------------------------------------------------------ 

def build_graph(data, start_date, end_date, cmt_weight, ism_weight, pr_weight, prm_weight):
    cmt_data, ism_data, pr_data, prm_data = data

    G = nx.Graph()
    # add nodes and edges to the snapshot_G graph based on the snapshot data
    snapshot_cmt = cmt_data[(cmt_data['timestamp'] >= start_date) & (cmt_data['timestamp'] <= end_date)] 
    snapshot_pr = pr_data[(pr_data['timestamp'] >= start_date) & (pr_data['timestamp'] <= end_date)] 
    snapshot_ism = ism_data[(ism_data['timestamp'] >= start_date) & (ism_data['timestamp'] <= end_date)] 
    snapshot_prm = prm_data[(prm_data['timestamp'] >= start_date) & (prm_data['timestamp'] <= end_date)] 

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

    return G



