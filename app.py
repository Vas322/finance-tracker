from flask import Flask, session, request, redirect, url_for
from config import Config


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY

    from routes.main import bp as main_bp
    from routes.operations import bp as operations_bp
    from routes.regular import bp as regular_bp
    from routes.settings import bp as settings_bp
    from routes.categories import bp as categories_bp
    from routes.budgets import bp as budgets_bp
    from routes.auth import bp as auth_bp
    from routes.analytics import bp as analytics_bp
    from routes.planning import bp as planning_bp
    from routes.vacations import bp as vacations_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(operations_bp)
    app.register_blueprint(regular_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(planning_bp)
    app.register_blueprint(vacations_bp)

    @app.before_request
    def check_auth():
        if request.endpoint and request.endpoint.startswith('auth.'):
            return
        if request.endpoint == 'static':
            return
        if not session.get('logged_in'):
            return redirect(url_for('auth.login', next=request.path))

    return app


app = create_app()

from database import init_db, backup_db
from apscheduler.schedulers.background import BackgroundScheduler


def check_regular_payments():
    from services.telegram_service import check_and_notify
    check_and_notify()


backup_db()
init_db()

scheduler = BackgroundScheduler()
scheduler.add_job(backup_db, 'cron', hour='6,18', minute=0)
scheduler.add_job(check_regular_payments, 'cron', hour='9', minute=0)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
