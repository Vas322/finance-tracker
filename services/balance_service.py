from datetime import date
from database import get_db, get_period_balance, set_period_balance
from services.period_service import get_period_dates, get_period, get_previous_period_dates


def get_expenses_for_period(start_date: date, end_date: date) -> int:
    with get_db() as conn:
        result = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM operations
            WHERE type = 'Расход' AND date >= ? AND date <= ?
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()
    return result['total']


def get_income_for_period(start_date: date, end_date: date) -> int:
    with get_db() as conn:
        result = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM operations
            WHERE type = 'Доход' AND date >= ? AND date <= ?
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()
    return result['total']


def update_period_balance(today: date):
    period_start, period_end = get_period_dates(today)
    period_name = get_period(today.strftime('%Y-%m-%d'))
    existing = get_period_balance(period_name, period_start.strftime('%Y-%m-%d'))
    if existing is None:
        prev_start, prev_end = get_previous_period_dates(today)
        
        with get_db() as conn:
            prev_period_name = get_period(prev_start.strftime('%Y-%m-%d'))
            prev_balance_result = conn.execute(
                'SELECT balance FROM period_balance WHERE period = ? AND start_date = ?',
                (prev_period_name, prev_start.strftime('%Y-%m-%d'))
            ).fetchone()
            prev_balance = prev_balance_result['balance'] if prev_balance_result else 0

            prev_income = get_income_for_period(prev_start, prev_end)
            prev_expenses = get_expenses_for_period(prev_start, prev_end)

            closing_balance = prev_balance + prev_income - prev_expenses

            set_period_balance(period_name, period_start.strftime('%Y-%m-%d'), closing_balance)
            return closing_balance
    return existing


def update_current_period_balance(today: date, new_balance: int):
    period_start, period_end = get_period_dates(today)
    period_name = get_period(today.strftime('%Y-%m-%d'))
    set_period_balance(period_name, period_start.strftime('%Y-%m-%d'), new_balance)
