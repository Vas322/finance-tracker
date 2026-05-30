from datetime import datetime, date
from config import SALARY_DAY, ADVANCE_DAY


def get_period(date_str):
    day = datetime.strptime(date_str, '%Y-%m-%d').day
    return "10-24" if 10 <= day <= 24 else "25-09"


def get_next_income_date(today):
    if today.day < SALARY_DAY:
        return date(today.year, today.month, SALARY_DAY)
    elif today.day < ADVANCE_DAY:
        return date(today.year, today.month, ADVANCE_DAY)
    else:
        next_month = today.month + 1
        year = today.year
        if next_month > 12:
            next_month = 1
            year += 1
        return date(year, next_month, SALARY_DAY)


def get_regular_payments_for_period(today, period_start_day, period_end_day):
    from database import get_db
    from datetime import datetime

    with get_db() as conn:
        payments = conn.execute('SELECT * FROM regular_payments').fetchall()

    total = 0
    for p in payments:
        if p['day'] and '-' in str(p['day']):
            payment_day = datetime.strptime(p['day'], '%Y-%m-%d').day
        else:
            payment_day = int(p['day']) if p['day'] else 1

        if period_start_day <= period_end_day:
            if period_start_day <= payment_day <= period_end_day:
                total += p['amount']
        else:
            if payment_day >= period_start_day or payment_day <= period_end_day:
                total += p['amount']
    return total


def get_regular_total_for_month():
    from database import get_db
    with get_db() as conn:
        result = conn.execute('SELECT SUM(amount) FROM regular_payments').fetchone()[0]
        return result or 0