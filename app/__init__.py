from flask import Flask
from .models import db
from .routes import init_routes
from config import Config


def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    init_routes(app)
    return app
