from flask import Flask
from .main import videos_bp 

def register_blueprints(app: Flask):
    app.register_blueprint(videos_bp, url_prefix='/videos')