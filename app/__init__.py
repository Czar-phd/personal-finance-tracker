from flask import Flask
from .routes import bp as main_bp

def create_app():
    app = Flask(__name__)
    # basic config placeholders
    app.config.update(
        SECRET_KEY="dev-secret-change-me",
        DEBUG=True,
        TESTING=False,
    )
    app.register_blueprint(main_bp)
    return app
