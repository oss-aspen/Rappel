import numpy as np
from dash import Input, Output, State, callback, dash
import datetime as dt
from data_utils.queries import fetch_data
from graph_utils.graph_helper import build_graph, apply_pagerank, find_threshold, draw_network


@callback(
    Output('animation-interval', 'disabled'),
    Output('animation-interval', 'interval'),
    Input('play-button', 'n_clicks'),
    Input('pause-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_animation(play_clicks, pause_clicks):
    """
    Control the animation based on play and pause button clicks.

    Args:
    -----
        play_clicks (int): The number of times the play button has been clicked.
        pause_clicks (int): The number of times the pause button has been clicked.

    Returns:
    --------
        tuple: A tuple containing two values:
               - bool: represents whether the animation interval should be disabled 
                       (True if disabled, False if enabled).
               - int: interval duration (in milliseconds) for the animation when it is enabled.
    """
    if dash.ctx.triggered_id == 'play-button':
        return False, 5000 # Enable the interval and set the interval duration (in milliseconds)
    return True, None # Disable the interval


@callback(
    Output('graph-slider', 'value'),
    Input('animation-interval', 'n_intervals'),
    State('graph-slider', 'value'),
    State('graph-slider', 'max'),
    prevent_initial_call=True
)
def update_slider_value(n_intervals, slider_value, slider_max):
    """
    Update the slider value with animation.

    Args:
    -----
        n_intervals (int): The number of times the animation interval has been triggered.
        slider_value (list): The current value of the graph slider, representing the selected time interval.
        slider_max (int): The maximum value of the graph slider, representing the maximum time interval.

    Returns:
    --------
        list: A list of two integers representing the updated value of the graph slider after each animation 
              interval trigger.

    Note:
    -----
    The function increments the slider value by one for each animation interval trigger. Once the slider value 
    reaches the maximum value, it resets to the minimum value, allowing the animation to loop through the time 
    intervals continuously.
    """
    new_value = [(slider_value[0] + 1) % (slider_max + 1), (slider_value[1] + 1) % (slider_max + 1)]
    return new_value


@callback(
    Output('graph-animation', 'figure'),
    Input('submit-button', 'n_clicks'),
    Input('graph-slider', 'value'),
    Input('animation-interval', 'n_intervals'),
    State('repo-org', 'value'),
    State('repo-name', 'value'),
    State('graph-slider', 'marks'),
    State('cmt-weight', 'value'), 
    State('ism-weight', 'value'), 
    State('pr-weight', 'value'), 
    State('prm-weight', 'value'),
    State('threshold-dropdown', 'value'), 
    State('number-input', 'value'),
    prevent_initial_call=True
)
def update_network(n_clicks, slider_value, n_intervals, repo_org, repo_name, marks, cmt_weight, ism_weight, pr_weight, prm_weight, threshold_type, threshold_value):
    """
    Build, update, and plot the network graph based on user input and animation intervals.

    Args:
    -----
        n_clicks (int): The number of times the submit button has been clicked.
        slider_value (list): The current value of the graph slider, representing the selected time interval.
        n_intervals (int): The number of times the animation interval has been triggered.
        repo_org (str): The organization name of the repository.
        repo_name (str): The name of the repository.
        marks (dict): A dictionary containing the time intervals as keys and their corresponding labels 
                      (formatted as "%m/%Y") as values.
        cmt_weight, ism_weight, pr_weight, prm_weight (float): The weights to assign to edges in 
                                                               the graph based on event type.
        threshold_type (str): The type of threshold for differentiating core and peripheral contributors 
                              (options: 'elbow', 'percentage', 'number').
        threshold_value (float): The value of the threshold based on the selected type.

    Returns:
    --------
        go.Figure: A Plotly Figure object representing the updated network graph visualization.
    """

    
    data = fetch_data(repo_org, repo_name) # fetch data from Augur
    marks = list(marks.values())
    # convert dates to dt.datetime objects
    start_date = dt.datetime.strptime(marks[slider_value[0]], "%m/%Y") 
    end_date = dt.datetime.strptime(marks[slider_value[1]], "%m/%Y")

    G = build_graph(data, start_date, end_date, cmt_weight, ism_weight, pr_weight, prm_weight) # use Augur data to create and populate nx.Graph object
    pagerank_scores, norm_scores = apply_pagerank(G) # pagerank scores for node size and color 

    # based on threshold type and value, calculate threshold score for core contributors 
    threshold_score = find_threshold(np.array(list(pagerank_scores.values())), [threshold_type, threshold_value]) 

    return draw_network(G, start_date, end_date, pagerank_scores, norm_scores, threshold_score)