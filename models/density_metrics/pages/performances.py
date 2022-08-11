import dash
dash.register_page(__name__, order=3)

from pandas import value_counts
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Output, Input

# Plotly theme
import plotly.io as pio
pio.templates.default = "plotly_white"

# Dataframe
from pages.df.df_performances import dframe_issue, dframe_pr


# layout of thrid (performance) tab ******************************************
layout = dbc.Card(
    [
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H4(id='pr_performance_output_container', children=[],
                            className = 'title_text',
                            style={"text-align": "center"}),
                dcc.Graph(id='p_graph1', figure={})
                ], width=6),
            dbc.Col([
                    html.H4(id='issue_performance_output_container', children=[],
                            className = 'title_text',
                            style={"text-align": "center"}),
                dcc.Graph(id='p_graph2', figure={})
            ], width=6),
            dbc.Col([
                    html.H4(id='pr_performance_output_subgraph_title',  children=[],
                    # html.H4('Selected on a repo to see the breakdown of PR performance',
                            className = 'title_text',
                            style={"text-align": "center"}),
                dcc.Graph(id='breakdown_performance', figure={})
            ], width=6),
            dbc.Col([
                    html.H4(id='issue_performance_output_subgraph_title',  children=[],
                    # html.H4('Selected on a repo to see the breakdown of issue performance',
                            className = 'title_text',
                            style={"text-align": "center"}),
                dcc.Graph(id='breakdown_performance2', figure={})
            ], width=6),
        ]),
        dcc.Markdown('''
            #### Performances Metrics:
            Performances metrics are the metrics for Pull Requests and Issue. Performances are calculated based on
            how fast the Pull Request/ Issue are closed. The faster a Pull Request/ Issue is closed, the higher weight
            it is within the calculation.

            Fast (closed within 30 days) = 1,
            Mild (closed within 60 days) = 0.66,
            Slow (closed within 90 days) = 0.33,
            Stale (closed more than 90 days) = 0.1

            PR/Issue opened within 45 days and are not yet closed are given 0.5, Hard-cap timeout = 365 days

            ''')
        ])
    ],
    color="light",
)

@callback(
    Output(component_id='pr_performance_output_container', component_property='children'),
    Output(component_id='issue_performance_output_container', component_property='children'),
    Output(component_id='p_graph1', component_property="figure"),
    Output(component_id="p_graph2", component_property="figure"),
    [Input(component_id='select_org', component_property='value')]
)

def update_graph(select_org):

    container_pr = 'Top 10 PR Performance in {}'.format(select_org)
    container_issue = 'Top 10 Issue Performance in {}'.format(select_org)

    df_pr = dframe_pr.groupby(['rg_name', 'repo_name']).sum().reset_index()
    pr_final = df_pr[df_pr['rg_name'] == select_org].sort_values(by='total', ascending=False)[:10]
    
    df_issue = dframe_issue.groupby(['rg_name', 'repo_name']).sum().reset_index()
    issue_final = df_issue[df_issue['rg_name'] == select_org].sort_values(by='total', ascending=False)[:10]

    piechart_pr = px.pie(
        data_frame=pr_final,
        values='total',
        names='repo_name',
        hole=.25
    )
    piechart_pr.update_traces(textposition='inside', textinfo='percent+label')
    piechart_pr.update_layout(
    # Add annotations in the center of the donut pies.
    annotations=[dict(text='PR', x=0.5, y=0.5, font_size=20, showarrow=False)])

    piechart_issue=px.pie(
        data_frame=issue_final,
        values='total',
        names='repo_name',
        hole=.25
    )
    piechart_issue.update_traces(textposition='inside', textinfo='percent+label')
    piechart_issue.update_layout(
    # Add annotations in the center of the donut pies.
    annotations=[dict(text='Issue', x=0.5, y=0.5, font_size=18, showarrow=False)])

    piechart_issue.update_traces(
            hovertemplate="<br>Repo: %{label} <br>PR Performance Score: %{value}<br><extra></extra>")
    piechart_pr.update_traces(
            hovertemplate="<br>Repo: %{label} <br>Issue Performance Score: %{value}<br><extra></extra>")


    return (container_pr, container_issue, piechart_pr, piechart_issue)


#---------------------------------------sub graph for PR---------------------------------------

@callback(
    Output(component_id='pr_performance_output_subgraph_title', component_property='children'),
    Output(component_id='breakdown_performance', component_property='figure'),
    Input(component_id='select_repo', component_property='value'),
    Input(component_id='select_org', component_property='value')
)

def update_side_graph1(select_repo, select_org):

    subgraph_title_pr = 'Breakdown of PR Performance - {}'.format(select_repo)

    df_org = dframe_pr[dframe_pr['rg_name'] == select_org]
    df_repo = df_org[df_org['repo_name'] == select_repo].groupby(['yearmonth', 'segment', 'color']).sum().reset_index()

    sub_piechart_pr = go.Figure(
                        data = [
                            go.Bar(
                                x = df_repo['yearmonth'].tolist(),
                                y = df_repo['num'].tolist(),
                                marker_color= df_repo['color'].tolist(),
                                text = df_repo['segment'].tolist()
                            )],
                        layout = dict(
                            title=f'{select_repo}'
                        )
    )
    sub_piechart_pr.update_traces(
        hovertemplate="<br>Segment: %{text} <br>Year/Month: %{x} <br>Amount: %{y}<br><extra></extra>")


    return subgraph_title_pr, sub_piechart_pr


#---------------------------------------sub graph for Issue---------------------------------------

@callback(
    Output(component_id='issue_performance_output_subgraph_title', component_property='children'),
    Output(component_id='breakdown_performance2', component_property='figure'),
    Input(component_id='select_repo', component_property='value'),
    Input(component_id='select_org', component_property='value')
)


def update_side_graph2(select_repo, select_org):

    subgraph_title_issue = 'Breakdown of Issue Performance - {}'.format(select_repo)

    df_org = dframe_issue[dframe_issue['rg_name'] == select_org]
    df_repo = df_org[df_org['repo_name'] == select_repo].groupby(['yearmonth', 'segment','color']).sum().reset_index()

    sub_piechart_issue = go.Figure(
                        data = [
                            go.Bar(
                                x = df_repo['yearmonth'].tolist(),
                                y = df_repo['num'].tolist(),
                                marker_color= df_repo['color'].tolist(),
                                text = df_repo['segment'].tolist()
                            )],
                        layout = dict(
                            title=f'{select_repo}'
                        ) 
    )

    sub_piechart_issue.update_traces(
        hovertemplate="<br>Segment: %{text} <br>Year/Month: %{x} <br>Amount: %{y}<br><extra></extra>")


    return subgraph_title_issue, sub_piechart_issue