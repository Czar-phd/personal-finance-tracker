from flask import Flask
from .routes import bp as main_bp
from .db import db

def create_app():
    application = Flask(__name__)
    application.config.update(
        SECRET_KEY="dev-secret-change-me",
        DEBUG=True,
        TESTING=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///app.sqlite3",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(application)

    # Register SQLAlchemy event listeners (touch updated_at on update)
    import app.model_events  # noqa: F401

    # Main JSON route
    application.register_blueprint(main_bp)

    # API (finance) routes
    from .finance.routes import bp as finance_bp
    application.register_blueprint(finance_bp, url_prefix="/api")

    # Web (HTML) dashboard
    from .web import bp as web_bp
    application.register_blueprint(web_bp)
    from .auth.routes import bp as auth_bp
    application.register_blueprint(auth_bp)

    # CLI commands
    from .cli.commands import register_cli
    register_cli(application)

    # ---- Flask-Login wiring ----
    from flask_login import LoginManager
    from .auth.models import User

    login_manager = LoginManager()
    login_manager.login_view = "main.index"
    login_manager.init_app(application)

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    return application
