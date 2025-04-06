from flask import Flask
from .main import public_bp 

def register_blueprints(app: Flask):
    app.register_blueprint(public_bp, url_prefix='/public')