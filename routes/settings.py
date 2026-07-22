from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app
from database import get_db, update_user_email, get_user
from config import Config
from datetime import date
from services.period_service import get_period_dates, get_salary_day, get_advance_day
from services.balance_service import update_period_balance
from services.telegram_service import send_message
from itsdangerous import URLSafeTimedSerializer
from decimal import Decimal

bp = Blueprint('settings', __name__)


def get_serializer():
    return URLSafeTimedSerializer(current_app.secret_key)


@bp.route('/income_settings', methods=['GET'])
def income_settings():
    return redirect(url_for('settings.profile'))


@bp.route('/profile', methods=['GET', 'POST'])
def profile():
    today = date.today()
    period_balance = update_period_balance(today)

    if request.method == 'POST':
        planned_salary = request.form.get('planned_salary', '').strip()
        salary_day = request.form.get('salary_day', '').strip()
        advance_day = request.form.get('advance_day', '').strip()
        email = request.form.get('email', '').strip().lower()

        with get_db() as conn:
            if planned_salary:
                conn.execute('UPDATE settings SET value = ? WHERE key = "planned_salary"', (planned_salary,))
            if salary_day:
                sd = int(salary_day)
                if 1 <= sd <= 31:
                    conn.execute('UPDATE settings SET value = ? WHERE key = "salary_day"', (str(sd),))
            if advance_day:
                ad = int(advance_day)
                if 1 <= ad <= 31:
                    conn.execute('UPDATE settings SET value = ? WHERE key = "advance_day"', (str(ad),))

        username = session.get('username', '')
        if username and email:
            update_user_email(username, email)

        flash('Настройки сохранены', 'success')
        return redirect(url_for('settings.profile'))

    with get_db() as conn:
        planned_salary = conn.execute('SELECT value FROM settings WHERE key = "planned_salary"').fetchone()
        user = get_user(session.get('username', ''))

    return render_template('profile.html',
                           planned_salary=float(planned_salary['value']) if planned_salary else Config.DEFAULT_PLANNED_SALARY / 100,
                           salary_day=get_salary_day(),
                           advance_day=get_advance_day(),
                           period_balance=period_balance,
                           user_email=user['email'] if user else '')


@bp.route('/send_reset_link', methods=['POST'])
def send_reset_link():
    username = session.get('username', '')
    if not username:
        flash('Ошибка: пользователь не найден', 'error')
        return redirect(url_for('auth.login'))

    user = get_user(username)
    if not user or not user['email']:
        flash('Сначала укажите email в личном кабинете', 'error')
        return redirect(url_for('settings.profile'))

    s = get_serializer()
    token = s.dumps(username, salt='password-reset')
    reset_link = url_for('auth.reset', token=token, _external=True)

    from services.mail_service import send_reset_email
    ok = send_reset_email(user['email'], reset_link)
    if ok:
        flash('Ссылка для смены пароля отправлена на ваш email', 'success')
    else:
        flash('Ошибка отправки письма. Попробуйте позже.', 'error')

    return redirect(url_for('settings.profile'))


@bp.route('/update_money', methods=['POST'])
def update_money():
    new_amount = int(Decimal(request.form['current_money']) * 100)
    today = date.today()
    from services.balance_service import update_current_period_balance
    update_current_period_balance(today, new_amount)
    flash(f'Начальный остаток: {new_amount//100:,.0f} ₽', 'success')
    return redirect(url_for('settings.profile'))


@bp.route('/test_telegram')
def test_telegram():
    ok = send_message('🔔 Тестовое уведомление из Finance Tracker')
    if ok:
        flash('Тестовое уведомление отправлено', 'success')
    else:
        flash('Ошибка отправки. Проверьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID', 'danger')
    return redirect(url_for('settings.profile'))
