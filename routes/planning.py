from flask import Blueprint, render_template
from database import get_db
from config import Config
from services.regular_service import get_regular_total, get_paid_regular_payments_in_period
from services.planning_service import get_planning_data
from services.period_service import get_period_dates
from datetime import date

bp = Blueprint('planning', __name__)


@bp.route('/budget_planning')
def budget_planning():
    today = date.today()
    months_ru = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    month_name = months_ru[today.month]

    with get_db() as conn:
        planned_salary_row = conn.execute(
            'SELECT value FROM settings WHERE key = "planned_salary"'
        ).fetchone()
        planned_salary = float(planned_salary_row['value']) if planned_salary_row else Config.DEFAULT_PLANNED_SALARY

        advance_row = conn.execute('''
            SELECT amount FROM operations
            WHERE type = 'Доход' AND category = 'Зарплата' AND subcategory = 'Аванс'
            ORDER BY date DESC LIMIT 1
        ''').fetchone()
        real_advance = advance_row['amount'] if advance_row else 0

    regular_total_month = get_regular_total(period_type='month')
    period_start, period_end = get_period_dates(today)
    paid_regular = get_paid_regular_payments_in_period(period_start, period_end)
    planning = get_planning_data(planned_salary, real_advance, regular_total_month, paid_regular)

    return render_template('budget_planning.html',
                           planning=planning,
                           regular_total_month=regular_total_month,
                           month_name=month_name)
