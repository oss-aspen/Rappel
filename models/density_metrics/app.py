
from subprocess import call
import dash_bootstrap_components as dbc
import dash
from dash import Dash, dcc, html, callback
from dash.dependencies import Output, Input

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

# import dataframe for options to the dropdown list
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
                            ["Select Github org and repo:"],
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
                                        ),
                                        dcc.Dropdown(
                                            id="select_repo",
                                            multi=False,
                                            clearable=True,
                                            disabled=False,
                                            style={"display": True},
                                            value="kubernetes",
                                            placeholder="Select Repository",
                                            options=[],
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


# cascading dropdown
@callback(Output("select_repo", "options"), Input("select_org", "value"))
def get_repo_options(select_org):
    org_data = dframe_perc[dframe_perc["org"] == select_org]
    return [{"label": i, "value": i} for i in org_data["repo"].unique()]


@callback(Output("select_repo", "value"),Input("select_repo", "options"))
def update_repo_value(select_repo):
    return [v["value"] for v in select_repo][0]



if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)