import dash_bootstrap_components as dbc
import dash
from dash import html
from dash import dcc
from dash.dependencies import Output, Input
from app import app

# Connect to the layout and callbacks of each tab
from activities import activities_layout
from communities import communities_layout
from performances import performances_layout
from df.df_activities import dframe_perc


# our app's Tabs *********************************************************
app_tabs = dbc.Container(
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

dropdown_layout = dbc.Container([
    dbc.Container([
        dbc.Container([
            dbc.Container([
            ], className = 'adjust_title'),
            dbc.Container([
                html.H5('Density of repo in an org', className = 'title_text'),

                dcc.Dropdown(id = 'select_org',
                             multi = False,
                             clearable = True,
                             disabled = False,
                             style = {'display': True},
                             value = 'kubernetes',
                             placeholder = 'Select Organization',
                             options = [{'label': c, 'value': c}
                                        for c in dframe_perc['org'].unique()], className = 'dcc_compon'),

                # dcc.Dropdown(id = 'select_repo',
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
    dbc.Container(id='content', children=[])

])


@app.callback(
    Output('select_repo', 'options'),
    Input('select_org', 'value'))
def get_country_options(select_org):
    org_data = dframe_perc[dframe_perc['org'] == select_org]
    return [{'label': i, 'value': i} for i in org_data['org'].unique()]


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