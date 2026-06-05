from flask import Flask, session, request, redirect, url_for
from routes.main import bp as main_bp
from routes.operations import bp as operations_bp
from routes.regular import bp as regular_bp
from routes.settings import bp as settings_bp
from routes.categories import bp as categories_bp
from routes.auth import bp as auth_bp
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['APP_PASSWORD'] = os.environ.get('APP_PASSWORD', 'admin123')

app.register_blueprint(main_bp)
app.register_blueprint(operations_bp)
app.register_blueprint(regular_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(auth_bp)


@app.before_request
def check_auth():
    if request.endpoint and request.endpoint.startswith('auth.'):
        return
    if request.endpoint == 'static':
        return
    if not session.get('logged_in'):
        return redirect(url_for('auth.login', next=request.path))


if __name__ == '__main__':
    from database import init_db
    init_db()
    app.run(debug=True)