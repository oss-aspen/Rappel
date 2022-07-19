import plotly.express as px
import dash_bootstrap_components as dbc
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input, State
from app import app
from df.df_activities import df4,drank


# layout of first (activity) tab ******************************************
activities_layout = html.Div([
    dbc.Row([
        dbc.Col([
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H5('Org Density by Activities', className = 'title_text'),
            dcc.Graph(id='scatter2', figure={})
        ], width=6),
        dbc.Col([
            html.H5('Density within an Organization', className = 'title_text'),
            dcc.Graph(id='scatter', figure={})
        ], width=6)
    ])
])

#-------------------------------------------------------------------------

@app.callback(
    Output(component_id='scatter2', component_property="figure"),
    Output(component_id="scatter", component_property="figure"),
    [Input(component_id='select_continent', component_property='value')]
)

def update_graph(select_continent):

    dff = df4[df4['org'] == select_continent]
    input_data = drank

    linechart = px.bar(
        data_frame=input_data,
        x="total_activity_score",
        y="org",
        orientation='h',
    )
    linechart.update_layout(yaxis={'categoryorder':'total ascending'})

    barchart=px.bar(
        data_frame=dff,
        x="org",
        y="percentage",
        color="repo_name",
        text="repo_name"
    )

    return (linechart, barchart)
