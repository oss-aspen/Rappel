from pandas import value_counts
import plotly.express as px
import dash_bootstrap_components as dbc
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input
from app import app
from df.df_performances import dframe_issue, dframe_pr


# layout of thrid (performance) tab ******************************************
performances_layout = html.Div([
    dbc.Row([
        dbc.Col([
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H5('PR Performance within an Organization', className = 'title_text'),
            dcc.Graph(id='p_graph1', figure={})
        ], width=6),
        dbc.Col([
            html.H5('Issue Performance within an Organization', className = 'title_text'),
            dcc.Graph(id='p_graph2', figure={})
        ], width=6)
    ])
])

@app.callback(
    Output(component_id='p_graph1', component_property="figure"),
    Output(component_id="p_graph2", component_property="figure"),
    [Input(component_id='select_continent', component_property='value')]
)

def update_graph(select_continent):

    test1 = dframe_pr.groupby(['rg_name', 'repo_name']).sum()
    test1 = test1.reset_index()
    pr_final = test1[test1['rg_name'] == select_continent].sort_values(by='total', ascending=False)[:10]
    
    test2 = dframe_issue.groupby(['rg_name', 'repo_name']).sum()
    test2 = test2.reset_index()
    issue_final = test2[test2['rg_name'] == select_continent].sort_values(by='total', ascending=False)[:10]

    piechart1 = px.pie(
        data_frame=pr_final,
        values='total',
        names='repo_name',
        hole=.25
    )
    piechart1.update_traces(textposition='inside', textinfo='percent+label')
    piechart1.update_layout(
    title_text="PR Performance",
    # Add annotations in the center of the donut pies.
    annotations=[dict(text='PR', x=0.5, y=0.5, font_size=20, showarrow=False)])

    piechart2=px.pie(
        data_frame=issue_final,
        values='total',
        names='repo_name',
        hole=.25
    )
    piechart2.update_traces(textposition='inside', textinfo='percent+label')
    piechart2.update_layout(
    title_text="Issue Performance",
    # Add annotations in the center of the donut pies.
    annotations=[dict(text='Issue', x=0.5, y=0.5, font_size=18, showarrow=False)])

    return (piechart1, piechart2)