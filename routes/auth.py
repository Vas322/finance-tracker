from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps

bp = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        app_password = request.args.get('app_password') or ''

        # Fallback: config might not be accessible from blueprint directly,
        # so read from Flask's current_app
        from flask import current_app
        correct = current_app.config.get('APP_PASSWORD', 'admin123')

        if password == correct:
            session['logged_in'] = True
            next_page = request.args.get('next', url_for('main.index'))
            return redirect(next_page)
        else:
            flash('Неверный пароль', 'error')

    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('auth.login'))
