import atexit
from flask import Flask, redirect, url_for
from config import Config
from extensions import db, login_manager, mail


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from auth import auth_bp
    from tasks import tasks_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    @app.route('/')
    def index():
        return redirect(url_for('tasks.index'))

    with app.app_context():
        import models  # noqa: F401 — registers user_loader
        db.create_all()

    from scheduler import init_scheduler
    scheduler = init_scheduler(app)
    atexit.register(lambda: scheduler.shutdown(wait=False))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
