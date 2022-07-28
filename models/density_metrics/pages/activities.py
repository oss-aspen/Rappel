import dash

dash.register_page(__name__, order=1, path='/')

import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Output, Input, State
from pages.df.df_activities import dframe_perc, breakdown_frame


# layout of first (activity) tab ******************************************
layout = dbc.Card(
    [
        dbc.CardBody(
            [
            dbc.Row([
                # dbc.Col([
                #     html.H5('Org Density by Activities', className = 'title_text'),
                #     dcc.Graph(id='scatter2', figure={})
                # ], width=6),
                dbc.Col([
                    html.H4('Density within an Organization',
                            className = 'title_text',
                            style={"text-align": "center"}),
                    dcc.Graph(id='scatter', figure={}, clickData=None, hoverData=None,
                    config={
                        'staticPlot': False,
                        'scrollZoom': True,
                        'doubleClick': 'reset',
                        'showTips': True
                    })
                ], width=6),
                dbc.Col([
                    html.H4('Selected Repo Breakdown in Activities By Time',
                            className = 'title_text',
                            style={"text-align": "center"}),
                    dcc.Graph(id='breakdown', figure={})
                ], width=6),
            dcc.Markdown('''
                #### Activities Metrics:
                Activities metrics are the metrics for activiness within each repo. Activities are calculated based on:
                
                weighted increment in star = 0.01,
                weighted increment in watcher = 0.1,
                weighted increment in fork = 0.2,
                weighted increment in issue = 0.5,
                weighted increment in Pull Request = 1,
                weighted increment in open Pull Request = 1.2,
                weighted increment in commit = 1.3,
                weighted increment in closed Pull Request = 1.5,
                weighted increment in committers = 1.6,
                weighted increment in merged Pull Request = 1.8

            ''')
            ])
        ])
    ],
    color="light",
)

#-------------------------------------------------------------------------building graph

@callback(
    # Output(component_id='scatter2', component_property="figure"),
    Output(component_id="scatter", component_property="figure"),
    [Input(component_id='select_org', component_property='value')]
)

def update_graph(select_org):

    dframe_org = dframe_perc[dframe_perc['org'] == select_org]
    # input_data = drank

    # linechart = px.bar(
    #     data_frame=input_data,
    #     x="total_activity_score",
    #     y="org",
    #     orientation='h',
    # )
    # linechart.update_layout(yaxis={'categoryorder':'total ascending'})

    barchart=px.bar(
        data_frame=dframe_org,
        x="org",
        y="percentage",
        color="repo_name",
        text="repo_name"
    )

    return (barchart)


#-----------------------------Breakdown Data------------------------------------
@callback(
    Output(component_id='breakdown', component_property='figure'),
    Input(component_id='scatter', component_property='hoverData'),
    Input(component_id='scatter', component_property='clickData'),
    Input(component_id='scatter', component_property='selectedData'),
    Input(component_id='select_org', component_property='value')
)

def update_side_graph(hov_data, clk_data, slct_data, select_org):
    if clk_data is None:
        dff1 = breakdown_frame[breakdown_frame['rg_name'] == 'kubernetes']
        dff2 = dff1[dff1['repo_name'] == 'kubernetes']
        fig2 = go.Figure(
            data = [
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['committer_increment'],
                    name='Increase in committer',
                    marker_color='indianred'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['open_pull_request_increment'],
                    name='Increase in open PR',
                    marker_color='lightsalmon'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['closed_pull_request_increment'],
                    name='Increase in closed PR',
                    marker_color='RoyalBlue'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['merged_pull_request_increment'],
                    name='Increase in merged PR',
                    marker_color='MediumPurple'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['issue_increment'],
                    name='Increase in issue',
                    marker_color='LightSeaGreen'
                )
            ]
        )

        return fig2
    
    else:

        clk_repo = clk_data['points'][0]['text']
        dff1 = breakdown_frame[breakdown_frame['rg_name'] == select_org]
        dff2 = dff1[dff1['repo_name'] == clk_repo].groupby(['rg_name', 'repo_name','yearmonth']).sum().reset_index()
        fig2 = go.Figure(
            data = [
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['committer_increment'],
                    name='Increase in committer',
                    marker_color='indianred'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['open_pull_request_increment'],
                    name='Increase in open PR',
                    marker_color='lightsalmon'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['closed_pull_request_increment'],
                    name='Increase in closed PR',
                    marker_color='RoyalBlue'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['merged_pull_request_increment'],
                    name='Increase in merged PR',
                    marker_color='MediumPurple'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['issue_increment'],
                    name='Increase in issue',
                    marker_color='LightSeaGreen'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['pull_request_increment'],
                    name='Increase in pr',
                    marker_color='lime'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['star_increment'],
                    name='Increase in star',
                    marker_color='aliceblue'
                ),
                go.Bar(
                    x=dff2['yearmonth'],
                    y=dff2['fork_increment'],
                    name='Increase in fork',
                    marker_color='cadetblue'
                ),
            ]
        )

        fig2.update_layout(title=f'{clk_repo}')

        return fig2
