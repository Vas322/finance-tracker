import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, session, request, redirect, url_for
from config import Config


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    app.config['WTF_CSRF_TIME_LIMIT'] = None

    from flask_wtf.csrf import CSRFProtect
    CSRFProtect(app)

    from extensions import limiter
    limiter.init_app(app)

    @app.template_filter('money')
    def money_format(value):
        return "{:,.0f}".format(value).replace(",", " ")

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
from services.backup_service import run_backup
from apscheduler.schedulers.background import BackgroundScheduler


def check_regular_payments():
    from services.telegram_service import notify_due_today
    notify_due_today()


def notify_upcoming_payments():
    from services.telegram_service import notify_tomorrow
    notify_tomorrow()


def daily_digest():
    from services.telegram_service import send_daily_digest
    send_daily_digest()


backup_db()  # local_db_backup
run_backup()
init_db()

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_backup, 'cron', hour='6,18', minute=0)
    scheduler.add_job(check_regular_payments, 'cron', hour='10', minute=0)
    scheduler.add_job(notify_upcoming_payments, 'cron', hour='21', minute=0)
    scheduler.add_job(daily_digest, 'cron', hour='9', minute=0)
    scheduler.start()

    from services.telegram_service import start_polling
    start_polling()

    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', use_reloader=False)
