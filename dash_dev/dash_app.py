"""
James: 
I got this from - https://dash.plotly.com/layout
"""
# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash import dcc, html
import plotly.express as px

import psycopg2
import numpy as np
import pandas as pd 
import sqlalchemy as salc
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime
plt.rcParams['figure.figsize'] = (15, 5)
import warnings
warnings.filterwarnings('ignore')

"""
    Connect to the database.
"""
with open("config_temp.json") as config_file:
    config = json.load(config_file)

database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})

"""
    Get the repo_id of the Augur repo by name.
"""
#add your repo name(s) here of the repo(s) you want to query if known (and in the database)
repo_name_set = ['augur']
repo_set = []

for repo_name in repo_name_set:
    repo_query = salc.sql.text(f"""
                 SET SCHEMA 'augur_data';
                 SELECT 
                    b.repo_id
                FROM
                    repo_groups a,
                    repo b
                WHERE
                    a.repo_group_id = b.repo_group_id AND
                    b.repo_name = \'{repo_name}\'
        """)

    t = engine.execute(repo_query)
    repo_id =t.mappings().all()[0].get('repo_id')
    repo_set.append(repo_id)

"""
    Get the files per PR from the Augur database query.
"""

df_pr_files = pd.DataFrame()
for repo_id in repo_set: 

    pr_query = salc.sql.text(f"""
                SELECT
					pr.pull_request_id AS pr_id,
                    prf.pr_file_id as file_id,
                    prf.pr_file_additions as additions,
                    prf.pr_file_deletions as deletions,
                    prf.pr_file_additions + prf.pr_file_deletions as total_changes,
                    pr.pr_created_at as created,
                    pr.pr_merged_at as merged,
                    pr.pr_closed_at as closed
                    
                FROM
                	repo r,
                    pull_requests pr,
                    pull_request_files prf

                WHERE
                	r.repo_id = pr.repo_id AND
                    r.repo_id = \'{repo_id}\' AND
                    prf.pull_request_id = pr.pull_request_id
                ORDER BY
                    pr_id
        """)
    df_current_repo = pd.read_sql(pr_query, con=engine)
    df_pr_files = pd.concat([df_pr_files, df_current_repo])

df_pr_files = df_pr_files.reset_index()
df_pr_files.drop("index", axis=1, inplace=True)
        
"""
    Which PR's were closed without being merged?
"""
df_pr_closed = df_pr_files[df_pr_files['merged'].isna() & df_pr_files['closed'].notna()]
df_pr_closed['close_window'] = df_pr_closed['closed'] - df_pr_closed['created']
df_pr_closed['close_window'] = df_pr_closed['close_window'].apply(lambda d: d.days + 1)

"""
    Do some data rearranging.
"""
# map the total number of lines changed per PR
df_pr_closed_fc = df_pr_closed.assign(sumChanges = df_pr_closed['pr_id'].map(df_pr_closed.groupby('pr_id')['total_changes'].sum()))

# drop any extra columns so we just see the PR, the days required to merge, and the number of changes made across all files.
df_pr_closed_fc = df_pr_closed_fc.drop(['file_id', 'additions', 'deletions', 'total_changes', 'created', 'merged', 'closed'], axis=1).drop_duplicates('pr_id')


"""
    This is the beginning of the Dash / Plotly code.
"""

app = dash.Dash(__name__)

df_pr_closed_fc["sumChanges"] = np.log(df_pr_closed_fc["sumChanges"])

fig = px.scatter(df_pr_closed_fc, x='close_window', y='sumChanges') 

app.layout = html.Div(children=[
    html.H1(children='Augur Demo Dash(board)'),

    html.Div(children='''
        Display Lines of code changed vs. days to close.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    """
    James:
    Small change here from the docs, exposing specific port here
    in the run_server line - 
    https://community.plotly.com/t/running-dash-app-in-docker-container/16067
    """
    app.run_server(host="0.0.0.0",debug=True, port=8050)
