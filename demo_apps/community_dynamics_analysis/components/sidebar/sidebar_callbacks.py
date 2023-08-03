from dash import dcc, html, Dash, Input, Output, State, callback
import datetime as dt
from dateutil.relativedelta import relativedelta 
#from app import app

#------------------------------------------------------ SLIDER MARKS ------------------------------------------------------ 
@callback(
    Output('graph-slider', 'marks'),
    Output('graph-slider', 'max'),
    Input('interval', 'value'), 
    State('time-period', 'value'), 
    prevent_initial_call = True
)
def generate_slider_marks(interval, dates):
    """
    Generate slider marks for the graph slider based on the selected time period.

    Args:
    -----
        interval (int): The number of months in the interval for the slider marks.
        dates (list): A list containing two date strings representing the start and end dates of the 
                      selected time period in the format "YYYY-MM-DD".

    Returns:
    --------
        dict: A dictionary representing the marks for the graph slider. The keys are integer indices 
              representing the positions of the slider, and the values are formatted date strings in the 
              format "MM/YYYY".
        int: The maximum value for the graph slider (represents the maximum position).
    """
    start_date = dt.datetime.strptime(dates[0],"%Y-%m-%d")
    end_date = dt.datetime.strptime(dates[1],"%Y-%m-%d")

    marks = {} # dict for slider marks
    current_date = start_date # start date
    index = 0

    while current_date <= end_date: 
        marks[index] = current_date.strftime("%m/%Y")
        current_date += relativedelta(months=interval)
        index += 1
    
    return marks, index-1

#------------------------------------------------------ THRESHOLD INPUT ------------------------------------------------------ 
@callback(
    Output('threshold-input', 'children'),
    [Input('threshold-dropdown', 'value')],
    prevent_initial_call=True
)
def update_threshold_input(value):
    """
    Update the threshold input options based on the selected threshold type from 
    dropdown menu (elbow, percentage, number).

    Args:
    -----
        value (str): The selected threshold type from the dropdown ('elbow', 'percentage', or 'number').

    Returns:
    --------
        html.Div: A Div component representing the input options for the selected threshold type. 
                  If 'elbow' is selected, no further input is required.
    """
    if value == 'elbow':
        return None
    elif value == 'percentage':
        return html.Div([
            html.Label("Percentage:"),
            dcc.Input(id='number-input', type='number', placeholder='Percentage')
        ])
    elif value == 'number':
        return html.Div([
            html.Label("Number:"),
            dcc.Input(id='number-input', type='number', placeholder='Number')
        ])