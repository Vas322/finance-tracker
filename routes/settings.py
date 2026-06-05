from flask import Blueprint, request, redirect, url_for, flash, render_template
from database import get_db

bp = Blueprint('settings', __name__)


@bp.route('/income_settings', methods=['GET'])
def income_settings():
    with get_db() as conn:
        planned_salary = conn.execute('SELECT value FROM settings WHERE key = "planned_salary"').fetchone()

    return render_template('income_settings.html',
                           planned_salary=float(planned_salary['value']) if planned_salary else 185000)


@bp.route('/save_income_settings', methods=['POST'])
def save_income_settings():
    planned_salary = request.form['planned_salary']

    with get_db() as conn:
        conn.execute('UPDATE settings SET value = ? WHERE key = "planned_salary"', (planned_salary,))

    flash('Настройки доходов сохранены', 'success')
    return redirect(url_for('settings.income_settings'))