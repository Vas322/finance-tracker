from datetime import date
from database import get_db, get_period_balance, set_period_balance
from services.period_service import get_period_dates, get_period


def get_expenses_for_period(start_date: date, end_date: date) -> int:
    with get_db() as conn:
        result = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM operations
            WHERE type = 'Расход' AND date >= ? AND date <= ?
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()
    return result['total']


def update_period_balance(today: date):
    period_start, period_end = get_period_dates(today)
    period_name = get_period(today.strftime('%Y-%m-%d'))
    existing = get_period_balance(period_name, period_start.strftime('%Y-%m-%d'))
    if existing is None:
        with get_db() as conn:
            result = conn.execute('''
                SELECT COALESCE(SUM(CASE WHEN type = 'Доход' THEN amount ELSE -amount END), 0) as balance
                FROM operations
                WHERE date < ?
            ''', (period_start.strftime('%Y-%m-%d'),)).fetchone()
            balance = result['balance']
        set_period_balance(period_name, period_start.strftime('%Y-%m-%d'), balance)
        return balance
    return existing


def get_income_for_period(start_date: date, end_date: date) -> int:
    with get_db() as conn:
        result = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM operations
            WHERE type = 'Доход' AND date >= ? AND date <= ?
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()
    return result['total']


def update_current_period_balance(today: date, new_balance: int):
    period_start, period_end = get_period_dates(today)
    period_name = get_period(today.strftime('%Y-%m-%d'))
    set_period_balance(period_name, period_start.strftime('%Y-%m-%d'), new_balance)
