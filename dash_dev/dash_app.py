"""
James: 
I got this from - https://dash.plotly.com/layout
"""
# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px

import db_new_issue_creators
import db_new_pr_submitters
import db_num_issues_open
import df_active_vs_drifting

"""
    This is the beginning of the Dash / Plotly code.
"""

app = dash.Dash(__name__)

app.layout = html.Div(children=[
            
    html.H1(children='Augur Community Dashboard'),

    html.Div(children='Select a repo to analyze:'),

    html.Div(id='current-project'),
    
    dcc.Dropdown(
        id='dropdown-label',
        options=[
            {'label': "Augur", 'value': 'augur'},
            {'label': "GrimoireLab", 'value': 'grimoirelab'}
        ],
        value='augur'
    ),

    html.Div([
        dcc.Graph(id='issue-creator-graph',
                    style={'width': '49%', 'display': 'inline-block'}),
        dcc.Graph(id='pr-submitter-graph',
                    style={'width': '49%', 'display': 'inline-block'})
    ]),

    dcc.Graph(id='num-issues-graph')
])


@app.callback(
    Output('current-project', 'children'),
    Input('dropdown-label', 'value'))
def display_current_project(label):
    return f"Current project is: {label}"

@app.callback(
    Output('issue-creator-graph', 'figure'),
    Input('dropdown-label', 'value'))
def get_issue_creator_dataframe(project_name):
    creator_df = db_new_issue_creators.new_issue_creators(project_name)
    return px.line(creator_df, 
                    x='created_at', 
                    y='index', 
                    title=f"# of New {project_name} Issue-Creators vs. Time",
                    labels={'created_at': 'Time (Months)', 'index': '# Individuals'})

@app.callback(
    Output('pr-submitter-graph', 'figure'),
    Input('dropdown-label', 'value'))
def get_pr_submitter_dataframe(project_name):
    submitter_df = db_new_pr_submitters.new_pr_submitters(project_name)
    return px.line(submitter_df,
                    x='pr_created_at', 
                    y='index', 
                    title=f'# Novel {project_name} PR Submitters vs. Time',
                    labels={'pr_created_at': 'Time (Months)', 'index': '# Individuals'})

@app.callback(
    Output('num-issues-graph', 'figure'),
    Input('dropdown-label', 'value')
)
def get_num_issues_dataframe(project_name):
    issues_df = db_num_issues_open.issues_open_over_time(project_name)
    return px.line(issues_df,
                    x='issue',
                    y='total',
                    title=f'# of Issues Open for {project_name}',
                    labels={'total': "# of Issues Open", 'issue': 'date'})

# @app.callback(
#     Output('active-drifting-pie', 'figure'),
#     Input('dropdown-label', 'value')
# )
# def get_active_drifting_dataframe_pie(project_name):
#     active_drifting_df = df_active_vs_drifting.get_df_active_drifting_users(project_name)
#     return px.pie(active_drifting_df,
#                     values='Count',
#                     names='Name',
#                     title=f'Active vs. Drifting Users for {project_name}')



if __name__ == '__main__':
    """
    James:
    Small change here from the docs, exposing specific port here
    in the run_server line - 
    https://community.plotly.com/t/running-dash-app-in-docker-container/16067
    """
    app.run_server(host="0.0.0.0",debug=True, port=8050)
