import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input
from app import app
from df.df_communities import df_pr_committers, df_pr_authors


# layout of second (community) tab ******************************************
communities_layout = html.Div([
    dbc.Row([
        dbc.Col([
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H5('Number of Committers by Month', className = 'title_text'),
            dcc.Graph(id='c_graph1', figure={})
        ], width=6),
        dbc.Col([
            html.H5('Number of Unique Committers by Month', className = 'title_text'),
            dcc.Graph(id='c_graph2', figure={})
        ], width=6)
    ]),
    dcc.Markdown('''
        #### Communities Metrics:
        Communities metrics are the display of # commits and # unique committers by org by month over time.
    ''')
])

@app.callback(
    Output(component_id='c_graph1', component_property="figure"),
    Output(component_id="c_graph2", component_property="figure"),
    [Input(component_id='select_continent', component_property='value')]
)

def update_graph(select_continent):

    dff = df_pr_committers[df_pr_committers['rg_name'] == select_continent]
    # input_data = df_pr_authors[df_pr_authors['rg_name'] == select_continent]

    barchart1 = px.bar(
        data_frame=dff,
        x="yearmonth",
        y="num_of_commit",
        color="repo_name",
        text="repo_name"
    )

    barchart2=px.bar(
        data_frame=dff,
        x="yearmonth",
        y="num_of_unique_commit",
        color="repo_name",
        text="repo_name"
    )

    return (barchart1, barchart2)