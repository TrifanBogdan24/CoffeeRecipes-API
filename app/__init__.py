from flask import Flask
from .web_api import web_api 

def create_app():
    app = Flask(__name__)
    app.register_blueprint(web_api)
    return app

