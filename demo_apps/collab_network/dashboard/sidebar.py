from dash import dcc, html, Dash, Input, Output, State
import dash_bootstrap_components as dbc
import dashboard.app as app
import datetime as dt
import dash_mantine_components as dmc
from dateutil.relativedelta import relativedelta 

sidebar_layout = html.Div(
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
                html.Label("Time period:  "),
                dmc.DateRangePicker(
                                        id="time-period",
                                        placeholder = "start date - end date",
                                        initialLevel = 'year',
                                        allowLevelChange = True,
                                        inputFormat = "MM/YYYY",
                                        minDate=dt.date(2005, 1, 1),
                                        maxDate=dt.date.today(),
                                        clearable=True,
                                        style = {"width":"auto", "font-size": "12px"}
                                    ),
                html.Br(),
                html.Label("Time Interval:  "),
                html.Br(),
                dcc.RadioItems(
                        id="interval", 
                        options =[{'label': '1 month', 'value': 1},
                                  {'label': '3 months', 'value': 3},
                                  {'label': '12 months', 'value': 12}],
                        inline = True
                    ),               
                html.Br(),
                html.Div([
                    html.H4([
                        html.Span(
                            "[i]",
                            id="threshold-tooltip",
                            style={"cursor": "pointer", "font-size": "12px", "margin-right": "5px", "color": "gray"},
                        ),
                        "Threshold Type"
                    ]),
                    dbc.Tooltip(
                        "The specified treshold type is used to identify the most important (core) contributors based on cenrality in the network ",
                        target="threshold-tooltip",
                        placement="bottom-start",
                        style={"background-color": "white", "color": "#000", "max-width": "300px"}
                    ),
                ]),
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
                dcc.Input(
                    id="number-input",
                    type="number",
                    placeholder="Number",
                    value=0,  # Set a default value for the number-input (if elbow is selected)
                    style={"display": "none"}  # Hide the input initially
                ),
                html.Br(),
                
                html.Div([
                    html.H4([
                        html.Span(
                            "[i]",
                            id="weights-tooltip",
                            style={"cursor": "pointer", "font-size": "12px", "margin-right": "5px", "color": "gray"},
                        ),
                        "Event Type Weights"
                    ]),
                    dbc.Tooltip(
                        "The weight of an event signifies the relative 'importance' of the type of interaction between two contributors",
                        target="weights-tooltip",
                        placement="bottom-start",
                        style={"background-color": "white", "color": "#000", "max-width": "300px"}
                    ),
                ]),
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

#------------------------------------------------------ CALLBACKS ------------------------------------------------------ 

# update slider
@app.callback(
    Output('graph-slider', 'marks'),
    Output('graph-slider', 'max'),
    Input('interval', 'value'), 
    State("time-period", "value"), 
    prevent_initial_call = True
)
def generate_slider_marks(interval, dates):
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


# get user input for threshold type and value
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
            dcc.Input(id='number-input', type='number', placeholder='Percentage')
        ])
    elif value == 'number':
        return html.Div([
            html.Label("Number:"),
            dcc.Input(id='number-input', type='number', placeholder='Number')
        ])