import dash
dash.register_page(__name__, order=2)

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, dash_table
from dash.dependencies import Output, Input

# Plotly theme
import plotly.io as pio
pio.templates.default = "plotly_white"

# Dataframe
from pages.df.df_communities import df_pr_committers


# layout of second (community) tab ******************************************
layout = dbc.Card(
    [
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H4(id='community_output_container', children=[],
                            className = 'title_text',
                            style={"text-align": "center"}),
                    dcc.Graph(id='c_graph2', figure={})
                ], width=20),
                dbc.Col([
                    html.H4(id='community_output_subgraph_title', children=[],
                            className = 'title_text',
                            style={"text-align": "center"}),
                    dcc.Graph(id='breakdown_commit', figure={})
                ], width=20),
            ]),
            dcc.Markdown('''
                #### Communities Metrics:
                Communities metrics are the display of the # unique committers by org by month over time.
                By clicking on different repos, a detailed breakdown table will show where the committers are from 
                and whether they are affiliated to a company or they are self contributors.
            ''')
        ])
    ],
    color="light",
)

#----------------------Call backs-------------------

@callback(
    Output(component_id='community_output_container', component_property='children'),
    Output(component_id="c_graph2", component_property="figure"),
    [Input(component_id='select_org', component_property='value')]
)

def update_graph(select_org):

    container = 'Number of Unique Committers - {}'.format(select_org)

    df_org = df_pr_committers[df_pr_committers['rg_name'] == select_org]
    # group by yearmonth and repo name to get the monthly unique committers.
    pr_committer_gb = df_org.groupby(['yearmonth', 'repo_name'])['num_of_unique_commit'].sum()
    pr_committer_gb = pr_committer_gb.to_frame().reset_index(drop=False, inplace=False).rename(columns={'num_of_unique_commit':'Number of Unique Committers'})

    barchart=px.bar(
        data_frame=pr_committer_gb,
        x="yearmonth",
        y="Number of Unique Committers",
        color="repo_name",
        text="repo_name"
    )

    barchart.update_traces(
            hovertemplate="<br>Repo: %{text} <br>Number of Unique Committers: %{y}<br><extra></extra>")


    return (container, barchart)


#--------------------breakdown graph-------------------
@callback(
Output(component_id='community_output_subgraph_title', component_property='children'),
Output(component_id='breakdown_commit', component_property='figure'),
Input(component_id='select_repo', component_property='value'),
Input(component_id='select_org', component_property='value')
)

# def update_side_graph(hov_data, clk_data, slct_data, select_org):
def update_side_graph(select_repo, select_org):

    subgraph_title = 'Number of Commits by Committer - {}'.format(select_repo)

    df_org = df_pr_committers[df_pr_committers['rg_name'] == select_org]
    df_repo = df_org[df_org['repo_name'] == select_repo]
    sub_frame = df_repo[["rg_name", "repo_name", 'yearmonth', 'cmt_committer_raw_email', 'cntrb_company', 'num_of_commit']]
    pvt_table = pd.pivot_table(sub_frame, values='num_of_commit',
                            index=['cmt_committer_raw_email', 'cntrb_company'],
                        columns=['yearmonth'], aggfunc=np.sum)
    pvt_table = pvt_table.fillna(0)
    pvt_table = pvt_table.reset_index().rename(columns={'2022-1':'Jan', '2022-2':'Feb', '2022-3':'Mar',
                                                '2022-4':'Apr', '2022-5':'May', '2022-6':'Jun',
                                                '2022-7':'Jul', '2022-8':'Aug'})


    table_fig = go.Figure(data=[go.Table(
            columnwidth = [30,30,30],
            header=dict(values=[col for col in pvt_table],
            line_color='darkslategray',
            align='center',
            font=dict(color='black', family="verdana", size=12),
            height=30
            ),
            cells = dict(values = [columnData.values for (columnName, columnData) in pvt_table.iteritems()],
                    line_color='darkslategray',
                    align='left',
                    height=30,
                    )
    )
    ])

    table_fig.update_layout(title=f'{select_repo}')

    return subgraph_title, table_fig