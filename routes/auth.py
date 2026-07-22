from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import check_password_hash
from database import get_user, create_user, get_user_by_email, update_user_password
from functools import wraps
from extensions import limiter
from itsdangerous import URLSafeTimedSerializer

bp = Blueprint('auth', __name__)


def get_serializer():
    return URLSafeTimedSerializer(current_app.secret_key)


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
        username = request.form.get('username', '').strip().lower()
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


@bp.route('/forgot', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def forgot():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Введите email', 'error')
            return render_template('forgot_password.html')

        user = get_user_by_email(email)
        if user:
            s = get_serializer()
            token = s.dumps(user['username'], salt='password-reset')
            reset_link = url_for('auth.reset', token=token, _external=True)

            from services.mail_service import send_reset_email
            ok = send_reset_email(email, reset_link)
            if ok:
                flash('Письмо со ссылкой для сброса пароля отправлено на ваш email', 'success')
            else:
                flash('Ошибка отправки письма. Попробуйте позже.', 'error')
        else:
            flash('Если этот email зарегистрирован, письмо будет отправлено', 'success')

        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')


@bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    s = get_serializer()
    try:
        username = s.loads(token, salt='password-reset', max_age=3600)
    except Exception:
        flash('Ссылка недействительна или истекла. Запросите новую.', 'error')
        return redirect(url_for('auth.forgot'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not password:
            flash('Введите новый пароль', 'error')
        elif password != confirm:
            flash('Пароли не совпадают', 'error')
        elif len(password) < 4:
            flash('Пароль должен быть минимум 4 символа', 'error')
        else:
            update_user_password(username, password)
            flash('Пароль успешно изменён. Войдите с новым паролем.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html')
