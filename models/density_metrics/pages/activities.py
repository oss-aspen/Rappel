import dash

dash.register_page(__name__, order=1, path='/')

import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Output, Input, State

# Plotly theme
import plotly.io as pio
pio.templates.default = "plotly_white"

# Dataframe
from pages.df.df_activities import dframe_perc, breakdown_frame


# layout of first (activity) tab ******************************************
layout = dbc.Card(
    [
        dbc.CardBody(
            [
            dbc.Row([
                dbc.Col([
                    html.H4(id='activity_output_container', children=[],
                            className = 'title_text',
                            style={"text-align": "center"}),
                    dcc.Graph(id='barplot', figure={}, clickData=None, hoverData=None,
                    config={
                        'staticPlot': False,
                        'scrollZoom': True,
                        'doubleClick': 'reset',
                        'showTips': True
                    })
                ], width=6),
                dbc.Col([
                    html.H4(id='activity_output_subgraph_title', children=[],
                            className = 'title_text',
                            style={"text-align": "center"}),
                    dcc.Graph(id='breakdown', figure={})
                ], width=6),
            dcc.Markdown('''
                #### Activities Metrics:
                Activities metrics are the metrics for activiness within each repo. Activities are calculated based on:
                
                weighted increment in issue = 0.5,
                weighted increment in Pull Request = 1,
                weighted increment in closed Pull Request = 1.5,
                weighted increment in merged Pull Request = 1.8

            ''')
            ])
        ])
    ],
    color="light",
)

#-------------------------------------------------------------------------building graph

@callback(
    Output(component_id='activity_output_container', component_property='children'),
    Output(component_id="barplot", component_property="figure"),
    [Input(component_id='select_org', component_property='value')]
)

def update_graph(select_org):

    container = 'Density within {}'.format(select_org)

    dframe_org = dframe_perc[dframe_perc['org'] == select_org]
    barchart=px.bar(
        data_frame=dframe_org,
        x="org",
        y="percentage",
        color="repo",
        text="repo"
    )

    return (container, barchart)


#---------------------------------Breakdown chart for repo activities-------------------------------
@callback(
    Output(component_id='activity_output_subgraph_title', component_property='children'),
    Output(component_id='breakdown', component_property='figure'),
    Input(component_id='select_repo', component_property='value'),
    Input(component_id='select_org', component_property='value')
)


def update_side_graph(select_repo, select_org):

    subgraph_title = 'Changes in Activity by Month - {}'.format(select_repo)

    df_org = breakdown_frame[breakdown_frame["rg_name"] == select_org]
    df_repo = df_org[df_org["repo_name"] == select_repo].groupby(["rg_name", "repo_name", "pr_yearmonth"]).sum().reset_index()
    breakdown_fig = go.Figure(
        data=[
            # go.Bar(
            #     x=df_repo["pr_yearmonth"],
            #     y=df_repo["commit_increment_number"],
            #     name="Commit",
            #     marker_color="red"
            # ),
            go.Bar(
                x=df_repo["pr_yearmonth"],
                y=df_repo["pr_increment_number"],
                name="PR",
                marker_color="lime"
            ),
            go.Bar(
                x=df_repo["pr_yearmonth"],
                y=df_repo["closed_pr_increment_number"],
                name="Closed PR",
                marker_color="cornflowerblue",
            ),
            go.Bar(
                x=df_repo["pr_yearmonth"],
                y=df_repo["merged_pr_increment_number"],
                name="Merged PR",
                marker_color="RoyalBlue",
            ),
            go.Bar(
                x=df_repo["pr_yearmonth"],
                y=df_repo["issue_increment_number"],
                name="Issue",
                marker_color="lightsalmon"
            ),
        ]
    )

    breakdown_fig.update_traces(
        hovertemplate="<br>Month: %{x} <br>Delta (△): %{y}<br><extra></extra>")
    breakdown_fig.update_layout(title=f"{select_repo}")

    return subgraph_title, breakdown_fig