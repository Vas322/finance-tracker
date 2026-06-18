from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from database import get_user, create_user
from functools import wraps
from extensions import limiter

bp = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = get_user(username)
        if user and check_password_hash(user['password_hash'], password):
            session['logged_in'] = True
            session['username'] = user['username']
            next_page = request.args.get('next', url_for('main.index'))
            return redirect(next_page)
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not username or not password:
            flash('Заполните все поля', 'error')
        elif password != confirm:
            flash('Пароли не совпадают', 'error')
        elif len(password) < 4:
            flash('Пароль должен быть минимум 4 символа', 'error')
        elif get_user(username):
            flash('Пользователь уже существует', 'error')
        else:
            if create_user(username, password):
                flash('Регистрация успешна. Войдите в систему.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Ошибка при регистрации', 'error')

    return render_template('register.html')


@bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('auth.login'))
