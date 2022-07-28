
from subprocess import call
import dash_bootstrap_components as dbc
import dash
from dash import Dash, dcc, html, callback
from dash.dependencies import Output, Input
import dash_labs as dl

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.SANDSTONE],
    suppress_callback_exceptions=True,
    meta_tags=[{
        "name": "viewport",
        "content": "width=device-width, initial-scale=1.0"
    }],
)

# Connect to the layout and callbacks of each tab
# from pages.activities import layout
# from pages.communities import layout
# from pages.performances import layout
from pages.df.df_activities import dframe_perc

# side bar code for page navigation
sidebar = html.Div(
    [
        html.H2("Pages", className="display-10"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(page["name"], href=page["path"])
                for page in dash.page_registry.values()
                if page["module"] != "pages.not_found_404"
            ],
            vertical=True,
            pills=True,
        ),
    ]
)

# app's Tabs *********************************************************
'''
app_tabs = dbc.Container(
    [
        dbc.Tabs(
            [
                dbc.Tab(
                    label="Activities",
                    tab_id="tab-activities",
                    labelClassName="text-success font-weight-bold",
                    activeLabelClassName="text-danger",
                ),
                dbc.Tab(
                    label="Communities",
                    tab_id="tab-communities",
                    labelClassName="text-success font-weight-bold",
                    activeLabelClassName="text-danger",
                ),
                dbc.Tab(
                    label="Performances",
                    tab_id="tab-performances",
                    labelClassName="text-success font-weight-bold",
                    activeLabelClassName="text-danger",
                ),
            ],
            id="tabs",
            active_tab="tab-activities",
        ),
    ],
    className="mt-3",
)
'''
# create a dropdown list to select organization
'''
dropdown_layout = dbc.Container(
    [
        dbc.Container(
            [
                dbc.Container(
                    [
                        dbc.Container([], className="adjust_title"),
                        dbc.Container(
                            [
                                html.Label("Select GitHub Org:", className="title_text"),
                                dcc.Dropdown(
                                    id="select_org",
                                    multi=False,
                                    clearable=True,
                                    disabled=False,
                                    style={"display": True},
                                    value="kubernetes",
                                    placeholder="Select Organization",
                                    options=[{"label": c, "value": c} for c in dframe_perc["org"].unique()],
                                    className="dcc_compon",
                                )
                            ],
                            className="adjust_drop_down_lists",
                        ),
                    ],
                    className="title_container twelve columns",
                )
            ],
            className="row flex-display",
        )
    ]
)
'''
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, width=1),
                dbc.Col(
                    [
                        html.H1("Org-repo Density Metrics", className="text-center"),

                        # search bar with buttons
                        html.Label(
                            ["Select Github repos or orgs:"],
                            style={"font-weight": "bold"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id="select_org",
                                            multi=False,
                                            clearable=True,
                                            disabled=False,
                                            style={"display": True},
                                            value="kubernetes",
                                            placeholder="Select Organization",
                                            options=[{"label": c, "value": c} for c in dframe_perc["org"].unique()],
                                        )
                                    ],
                                    style={
                                        "width": "50%",
                                        "display": "table-cell",
                                        "verticalAlign": "middle",
                                        "padding-right": "10px",
                                    },
                                ),
                                dbc.Button(
                                    "Search",
                                    id="search",
                                    n_clicks=0,
                                    class_name="btn btn-primary",
                                    style={
                                        "verticalAlign": "top",
                                        "display": "table-cell",
                                    },
                                ),
                            ],
                            style={
                                "align": "right",
                                "display": "table",
                                "width": "60%",
                            },
                        ),
                        dcc.Loading(
                            children=[html.Div(id="results-output-container", className="mb-4")],
                            color="#119DFF",
                            type="dot",
                            fullscreen=True,
                        ),
                        # dbc.Row(dbc.Col(dropdown_layout, width=12), className="mb-3"),
                        # dbc.Container(id="content", children=[]),
                        dash.page_container,
                    ],
                    width={"size": 11},
                )
            ],
            ),
        ],
        fluid=True,
        className="dbc",
        style={"padding-top": "1em"},
    )



@callback(Output("select_repo", "options"), Input("select_org", "value"))
def get_country_options(select_org):
    org_data = dframe_perc[dframe_perc["org"] == select_org]
    return [{"label": i, "value": i} for i in org_data["org"].unique()]

'''
@callback(Output("content", "children"), [Input("tabs", "active_tab")])
def switch_tab(tab_chosen):
    if tab_chosen == "tab-activities":
        return layout
    elif tab_chosen == "tab-communities":
        return layout
    elif tab_chosen == "tab-performances":
        return layout
    return html.P("This shouldn't be displayed for now...")
'''


if __name__ == "__main__":
    app.run(debug=True,)