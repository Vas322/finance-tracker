from flask import render_template
from database import get_db, get_current_money
from utils import get_next_income_date, get_regular_payments_for_period, get_regular_total_for_month
from config import SALARY_DAY, ADVANCE_DAY
from datetime import date


def register_routes(app):
    @app.route('/')
    def index():
        today = date.today()
        current_money = get_current_money()

        with get_db() as conn:
            operations = conn.execute('SELECT * FROM operations ORDER BY date DESC LIMIT 30').fetchall()
            total_income = \
            conn.execute('SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Доход"').fetchone()[0]
            total_expense = \
            conn.execute('SELECT COALESCE(SUM(amount), 0) FROM operations WHERE type="Расход"').fetchone()[0]
            balance = total_income - total_expense

        # Определяем текущий период
        if 10 <= today.day <= 24:
            period_start, period_end = 10, 24
        else:
            period_start, period_end = 25, 9

        regular_this_period = get_regular_payments_for_period(today, period_start, period_end)
        regular_total = get_regular_total_for_month()

        # Свободные деньги
        free_money = current_money + total_income - total_expense - regular_this_period

        # Светофор
        if free_money < 0:
            traffic_light = "red"
            traffic_text = "⚠️ КАССОВЫЙ РАЗРЫВ!"
        elif free_money < 5000:
            traffic_light = "yellow"
            traffic_text = "⚠️ Осторожно: остаток меньше 5000 ₽"
        else:
            traffic_light = "green"
            traffic_text = "✅ Всё хорошо"

        next_income = get_next_income_date(today)
        days_to_income = (next_income - today).days

        return render_template('index.html',
                               operations=operations,
                               total_income=total_income,
                               total_expense=total_expense,
                               balance=balance,
                               free_money=free_money,
                               days_to_income=days_to_income,
                               next_income=next_income,
                               traffic_light=traffic_light,
                               traffic_text=traffic_text,
                               regular_total=regular_total,
                               regular_this_period=regular_this_period,
                               current_money=current_money)
