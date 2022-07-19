import dash_bootstrap_components as dbc
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input
from app import app

# Connect to the layout and callbacks of each tab
from activities import activities_layout
from communities import communities_layout
from performances import performances_layout
from df.df_activities import df4


# our app's Tabs *********************************************************
app_tabs = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(label="Activities", tab_id="tab-activities", labelClassName="text-success font-weight-bold", activeLabelClassName="text-danger"),
                dbc.Tab(label="Communities", tab_id="tab-communities", labelClassName="text-success font-weight-bold", activeLabelClassName="text-danger"),
                dbc.Tab(label="Performances", tab_id="tab-performances", labelClassName="text-success font-weight-bold", activeLabelClassName="text-danger"),
            ],
            id="tabs",
            active_tab="tab-activities",
        ),
    ], className="mt-3"
)

dropdown_layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
            ], className = 'adjust_title'),
            html.Div([
                html.H5('Density of repo in an org', className = 'title_text'),

                dcc.Dropdown(id = 'select_continent',
                             multi = False,
                             clearable = True,
                             disabled = False,
                             style = {'display': True},
                             value = 'kubernetes',
                             placeholder = 'Select Organization',
                             options = [{'label': c, 'value': c}
                                        for c in df4['org'].unique()], className = 'dcc_compon'),

                # dcc.Dropdown(id = 'select_countries',
                #              multi = True,
                #              clearable = True,
                #              disabled = False,
                #              style = {'display': True},
                #              placeholder = 'Select Repo',
                #              options = [], className = 'dcc_compon'),

            ], className = 'adjust_drop_down_lists')
        ], className = "title_container twelve columns")
    ], className = "row flex-display")

])

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Org-repo Density Metrics",
                            style={"textAlign": "center"}), width=12)),
    dbc.Row(dbc.Col(dropdown_layout, width=12), className="mb-3"),
    dbc.Row(dbc.Col(app_tabs, width=12), className="mb-3"),
    html.Div(id='content', children=[])

])


@app.callback(
    Output('select_countries', 'options'),
    Input('select_continent', 'value'))
def get_country_options(select_continent):
    data1 = df4[df4['org'] == select_continent]
    return [{'label': i, 'value': i} for i in data1['org'].unique()]


@app.callback(
    Output("content", "children"),
    [Input("tabs", "active_tab")]
)
def switch_tab(tab_chosen):
    if tab_chosen == "tab-activities":
        return activities_layout
    elif tab_chosen == "tab-communities":
        return communities_layout
    elif tab_chosen == "tab-performances":
        return performances_layout
    return html.P("This shouldn't be displayed for now...")



if __name__=='__main__':
    app.run_server(debug=True, port = 8053)