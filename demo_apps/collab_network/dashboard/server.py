from flask import Flask
from dash import Dash

server = Flask('dashboard')
app = Dash(server=server)