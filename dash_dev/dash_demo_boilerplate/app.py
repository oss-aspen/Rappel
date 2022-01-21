import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# create an app class
app = dash.Dash(__name__)

# define the html layout of the app
app.layout = html.Div(children=[
    html.H1(children="Hello World!"),
    html.H2(children=[
        html.H3(children="From James"),
        html.H3(children="And Cali")
    ])
])

if __name__ == "__main__":
    # run the app as a server
    app.run_server(host="0.0.0.0", port=8050, debug=True)