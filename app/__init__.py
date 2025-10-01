from flask import Flask
from .routes import bp as main_bp
from .db import db

def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="dev-secret-change-me",
        DEBUG=True,
        TESTING=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///app.sqlite3",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)

    # main JSON route
    app.register_blueprint(main_bp)

    # API (finance) routes
    from .finance.routes import bp as finance_bp
    app.register_blueprint(finance_bp, url_prefix="/api")

    # CLI commands
    from .cli.commands import register_cli
    register_cli(app)

    # Web (HTML) dashboard
    from .web import bp as web_bp
    app.register_blueprint(web_bp)

    return app
